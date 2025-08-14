from typing import Dict, Any, Optional  # ADD Optional here
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from src.controllers.ai_models.base_ai_controller import BaseAIController
from src.services.ai_models.long_form_book_service import LongFormBookService
from src.models.ai_models.long_form_book import LongFormBookRequest
from src.models.ai_models.usage_history import UsageStatus
from src.controllers.ai_models.settings_controller import AIModelSettingsController
from src.controllers.ai_models.ai_usage_controller import AIUsageController
from src.config.mongodb import MongoDB
from datetime import datetime
from bson import ObjectId
import logging
import json

logger = logging.getLogger(__name__)

class LongFormBookController(BaseAIController):
    def __init__(self):
        super().__init__("long-form-book")
        self.service = LongFormBookService()
        self.usage_controller = AIUsageController()

    def _flatten_nested_data(self, nested_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert nested frontend data to flat structure expected by Pydantic model"""
        flat_data = {}
        
        for section_key, section_data in nested_data.items():
            if isinstance(section_data, dict):
                for field_key, field_value in section_data.items():
                    flat_data[field_key] = field_value
            else:
                flat_data[section_key] = section_data
        
        return flat_data

    def _get_user_query(self, user_id: str) -> dict:
        """Create MongoDB query for user ID (handles both string and ObjectId)"""
        try:
            # Try to convert to ObjectId first
            return {"_id": ObjectId(user_id)}
        except:
            # If it fails, use as string
            return {"_id": user_id}

    async def check_credits(self, current_user: str) -> Dict[str, Any]:
        """Check if user has sufficient credits before starting generation"""
        try:
            # Get user credits
            users_collection = await MongoDB.get_collection("users")
            user_query = self._get_user_query(current_user)
            user = await users_collection.find_one(user_query)
            
            if not user:
                return {
                    "status": 404,
                    "success": False,
                    "message": "User not found",
                    "data": {}
                }
            
            user_credits = user.get("credits", 0)
            credits_required = 50
            
            return {
                "status": 200,
                "success": True,
                "message": "Credit check completed",
                "data": {
                    "user_credits": user_credits,
                    "credits_required": credits_required,
                    "has_sufficient_credits": user_credits >= credits_required,
                    "credits_needed": max(0, credits_required - user_credits)
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking credits: {str(e)}")
            return {
                "status": 500,
                "success": False,
                "message": f"Failed to check credits: {str(e)}",
                "data": {}
            }

    async def process_request_stream(self, request_data: Dict[str, Any], current_user: str) -> StreamingResponse:
        """Process long-form book generation request with Server-Sent Events streaming"""
        
        async def generate_stream():
            usage_id = None
            final_book_data = None
            
            try:
                # Step 1: Dynamic validation
                settings_controller = AIModelSettingsController()
                validation_result = await settings_controller.validate_user_input(
                    "long-form-book", 
                    request_data
                )
                
                if not validation_result["valid"]:
                    data = json.dumps({
                        "type": "error",
                        "error_code": "VALIDATION_ERROR",
                        "message": "Invalid input parameters",
                        "errors": validation_result["errors"]
                    })
                    yield f"event: error\ndata: {data}\n\n"
                    return
                
                # Step 2: Flatten and create request object
                flat_data = self._flatten_nested_data(validation_result["validated_data"])
                book_request = LongFormBookRequest(**flat_data)

                # Step 3: Early credit check and usage record creation
                try:
                    usage_id = await self.create_usage_record(
                        user_id=current_user,
                        request_data=book_request.dict(),
                        credits_required=50
                    )
                except HTTPException as e:
                    # Handle insufficient credits error
                    if e.status_code == 400 and "Insufficient credits" in str(e.detail):
                        # Get user's actual credits for response
                        credit_info = await self.check_credits(current_user)
                        user_credits = credit_info.get("data", {}).get("user_credits", 0)
                        
                        data = json.dumps({
                            "type": "error",
                            "error_code": "INSUFFICIENT_CREDITS",
                            "message": "You don't have enough credits to generate this book. Please recharge your account.",
                            "credits_required": 50,
                            "credits_available": user_credits,
                            "credits_needed": max(0, 50 - user_credits)
                        })
                        yield f"event: error\ndata: {data}\n\n"
                        return
                    else:
                        # Other errors
                        data = json.dumps({
                            "type": "error",
                            "error_code": "SYSTEM_ERROR",
                            "message": f"System error: {e.detail}"
                        })
                        yield f"event: error\ndata: {data}\n\n"
                        return
                except Exception as e:
                    data = json.dumps({
                        "type": "error",
                        "error_code": "UNKNOWN_ERROR",
                        "message": f"Unexpected error: {str(e)}"
                    })
                    yield f"event: error\ndata: {data}\n\n"
                    return

                # Step 4: Update status to processing
                await self.update_usage_record(
                    usage_id=usage_id,
                    response_data={},
                    status=UsageStatus.PROCESSING
                )

                # Step 5: Send initial success message
                data = json.dumps({
                    "type": "credits_deducted",
                    "message": "Credits deducted successfully. Starting book generation...",
                    "usage_id": usage_id,
                    "credits_used": 50
                })
                yield f"event: credits_deducted\ndata: {data}\n\n"

                # Step 6: Stream book generation
                try:
                    async for chunk in self.service.generate_book_stream(book_request):
                        # Parse the existing JSON chunk
                        try:
                            chunk_data = json.loads(chunk.strip())
                            event_type = chunk_data.get("type", "message")
                            
                            # Format as Server-Sent Event
                            yield f"event: {event_type}\ndata: {json.dumps(chunk_data)}\n\n"
                            
                            # Check if this is the final completion chunk
                            if chunk_data.get("type") == "complete":
                                final_book_data = chunk_data.get("book_data", {})
                        except json.JSONDecodeError:
                            # If not valid JSON, send as generic message
                            yield f"event: message\ndata: {json.dumps({'message': chunk.strip()})}\n\n"

                except Exception as e:
                    logger.error(f"Error during book generation: {str(e)}")
                    
                    # Update usage record with error
                    if usage_id:
                        await self.update_usage_record(
                            usage_id=usage_id,
                            response_data={},
                            status=UsageStatus.FAILED,
                            error_message=str(e)
                        )
                    
                    data = json.dumps({
                        "type": "error",
                        "error_code": "GENERATION_ERROR",
                        "message": f"Book generation failed: {str(e)}",
                        "usage_id": usage_id
                    })
                    yield f"event: error\ndata: {data}\n\n"
                    return

                # Step 7: Store complete book data in database
                if final_book_data and usage_id:
                    try:
                        # Prepare comprehensive response data for storage
                        response_data = {
                            "book_metadata": final_book_data.get("metadata", {}),
                            "table_of_contents": final_book_data.get("table_of_contents", []),
                            "chapters_summary": final_book_data.get("chapters_summary", []),
                            "pdf_base64": final_book_data.get("pdf_base64", ""),
                            "full_book_content": final_book_data.get("full_book_data", {}),
                            "generation_completed": True,
                            "stored_at": datetime.utcnow().isoformat(),
                            "total_words": final_book_data.get("metadata", {}).get("total_words", 0),
                            "total_images": final_book_data.get("metadata", {}).get("total_images", 0),
                            "generation_time": final_book_data.get("metadata", {}).get("generation_time", 0)
                        }

                        # Update usage record with complete data
                        await self.update_usage_record(
                            usage_id=usage_id,
                            response_data=response_data,
                            status=UsageStatus.COMPLETED
                        )

                        # Send final confirmation
                        data = json.dumps({
                            "type": "stored",
                            "message": "Book successfully stored in database",
                            "usage_id": usage_id,
                            "storage_info": {
                                "total_size": len(json.dumps(response_data)),
                                "pdf_size": len(final_book_data.get("pdf_base64", "")),
                                "chapters_count": len(final_book_data.get("full_book_data", {}).get("chapters", [])),
                                "images_count": final_book_data.get("metadata", {}).get("total_images", 0)
                            }
                        })
                        yield f"event: stored\ndata: {data}\n\n"

                    except Exception as e:
                        logger.error(f"Error storing book data: {str(e)}")
                        data = json.dumps({
                            "type": "error",
                            "error_code": "STORAGE_ERROR",
                            "message": f"Book generated but failed to store: {str(e)}",
                            "usage_id": usage_id
                        })
                        yield f"event: error\ndata: {data}\n\n"

            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                
                # Update usage record with error if usage_id exists
                if usage_id:
                    try:
                        await self.update_usage_record(
                            usage_id=usage_id,
                            response_data={},
                            status=UsageStatus.FAILED,
                            error_message=str(e)
                        )
                    except:
                        pass
                
                data = json.dumps({
                    "type": "error",
                    "error_code": "FATAL_ERROR", 
                    "message": f"Fatal error during generation: {str(e)}",
                    "error": str(e),
                    "usage_id": usage_id
                })
                yield f"event: error\ndata: {data}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )

    async def get_stored_book(self, usage_id: str, current_user: str) -> Dict[str, Any]:
        """Get complete stored book data including PDF"""
        try:
            usage_detail = await self.usage_controller.get_usage_detail(usage_id, current_user)
            
            if not usage_detail.output_data:
                return {
                    "status": 404,
                    "success": False,
                    "message": "Book data not found or not yet generated",
                    "data": {}
                }
            
            # Check if generation was completed
            if usage_detail.status != UsageStatus.COMPLETED:
                return {
                    "status": 202,
                    "success": False,
                    "message": f"Book generation is {usage_detail.status.value}. Please wait for completion.",
                    "data": {
                        "status": usage_detail.status.value,
                        "created_at": usage_detail.created_at,
                        "usage_id": usage_id
                    }
                }
            
            # Return complete book data including PDF
            return {
                "status": 200,
                "success": True,
                "message": "Stored book retrieved successfully",
                "data": {
                    "usage_id": usage_id,
                    "book_metadata": usage_detail.output_data.get("book_metadata", {}),
                    "table_of_contents": usage_detail.output_data.get("table_of_contents", []),
                    "full_book_content": usage_detail.output_data.get("full_book_content", {}),
                    "pdf_base64": usage_detail.output_data.get("pdf_base64", ""),
                    "chapters_summary": usage_detail.output_data.get("chapters_summary", []),
                    "generation_info": {
                        "created_at": usage_detail.created_at,
                        "completed_at": usage_detail.completed_at,
                        "status": usage_detail.status.value,
                        "credits_used": usage_detail.credits_used,
                        "generation_time": usage_detail.output_data.get("generation_time", 0),
                        "total_words": usage_detail.output_data.get("total_words", 0),
                        "total_images": usage_detail.output_data.get("total_images", 0)
                    },
                    "storage_info": {
                        "stored_at": usage_detail.output_data.get("stored_at"),
                        "total_size": len(json.dumps(usage_detail.output_data)),
                        "has_pdf": bool(usage_detail.output_data.get("pdf_base64")),
                        "has_full_content": bool(usage_detail.output_data.get("full_book_content"))
                    }
                }
            }
            
        except ValueError as e:
            return {
                "status": 404,
                "success": False,
                "message": str(e),
                "data": {}
            }
        except Exception as e:
            logger.error(f"Error retrieving stored book: {str(e)}")
            return {
                "status": 500,
                "success": False,
                "message": f"Failed to retrieve stored book: {str(e)}",
                "data": {}
            }

    async def get_book_pdf(self, usage_id: str, current_user: str) -> Dict[str, Any]:
        """Get only the PDF for download"""
        try:
            usage_detail = await self.usage_controller.get_usage_detail(usage_id, current_user)
            
            if not usage_detail.output_data:
                return {
                    "status": 404,
                    "success": False,
                    "message": "Book not found",
                    "data": {}
                }
            
            if usage_detail.status != UsageStatus.COMPLETED:
                return {
                    "status": 202,
                    "success": False,
                    "message": f"Book generation is {usage_detail.status.value}. PDF not yet available.",
                    "data": {
                        "status": usage_detail.status.value,
                        "usage_id": usage_id
                    }
                }
            
            pdf_base64 = usage_detail.output_data.get("pdf_base64", "")
            if not pdf_base64:
                return {
                    "status": 404,
                    "success": False,
                    "message": "PDF not found or not generated",
                    "data": {}
                }
            
            # Get book title for filename
            book_metadata = usage_detail.output_data.get("book_metadata", {})
            book_title = book_metadata.get("title", "book")
            
            # Clean filename
            safe_filename = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_filename = safe_filename.replace(' ', '_')[:50]  # Limit length
            
            return {
                "status": 200,
                "success": True,
                "message": "PDF retrieved successfully",
                "data": {
                    "pdf_base64": pdf_base64,
                    "filename": f"{safe_filename}.pdf",
                    "book_title": book_title,
                    "file_size": len(pdf_base64),
                    "generated_at": usage_detail.completed_at,
                    "book_info": {
                        "author": book_metadata.get("author", ""),
                        "genre": book_metadata.get("genre", ""),
                        "total_pages": book_metadata.get("total_pages", 0),
                        "total_words": book_metadata.get("total_words", 0)
                    }
                }
            }
            
        except ValueError as e:
            return {
                "status": 404,
                "success": False,
                "message": str(e),
                "data": {}
            }
        except Exception as e:
            logger.error(f"Error retrieving PDF: {str(e)}")
            return {
                "status": 500,
                "success": False,
                "message": f"Failed to retrieve PDF: {str(e)}",
                "data": {}
            }

    async def get_generation_status(self, usage_id: str, current_user: str) -> Dict[str, Any]:
        """Get current status of book generation"""
        try:
            usage_detail = await self.usage_controller.get_usage_detail(usage_id, current_user)
            
            return {
                "status": 200,
                "success": True,
                "message": "Generation status retrieved successfully",
                "data": {
                    "usage_id": usage_id,
                    "status": usage_detail.status.value,
                    "created_at": usage_detail.created_at,
                    "started_at": usage_detail.started_at,
                    "completed_at": usage_detail.completed_at,
                    "credits_used": usage_detail.credits_used,
                    "error_message": usage_detail.error_message,
                    "has_output": bool(usage_detail.output_data),
                    "progress_info": {
                        "is_pending": usage_detail.status == UsageStatus.PENDING,
                        "is_processing": usage_detail.status == UsageStatus.PROCESSING,
                        "is_completed": usage_detail.status == UsageStatus.COMPLETED,
                        "is_failed": usage_detail.status == UsageStatus.FAILED,
                        "is_cancelled": usage_detail.status == UsageStatus.CANCELLED
                    },
                    "estimated_completion": self._calculate_estimated_completion(usage_detail)
                }
            }
            
        except ValueError as e:
            return {
                "status": 404,
                "success": False,
                "message": str(e),
                "data": {}
            }
        except Exception as e:
            logger.error(f"Error getting generation status: {str(e)}")
            return {
                "status": 500,
                "success": False,
                "message": f"Failed to get generation status: {str(e)}",
                "data": {}
            }

    def _calculate_estimated_completion(self, usage_detail) -> Optional[str]:
        """Calculate estimated completion time for processing books"""
        if usage_detail.status != UsageStatus.PROCESSING:
            return None
        
        if not usage_detail.started_at:
            return None
        
        # Estimate based on average generation time (15-30 minutes)
        elapsed_minutes = (datetime.utcnow() - usage_detail.started_at).total_seconds() / 60
        estimated_total_minutes = 22.5  # Average of 15-30 minutes
        
        if elapsed_minutes >= estimated_total_minutes:
            return "Soon"
        else:
            remaining_minutes = estimated_total_minutes - elapsed_minutes
            return f"~{int(remaining_minutes)} minutes"

    async def cancel_generation(self, usage_id: str, current_user: str) -> Dict[str, Any]:
        """Cancel an ongoing book generation"""
        try:
            usage_detail = await self.usage_controller.get_usage_detail(usage_id, current_user)
            
            if usage_detail.status not in [UsageStatus.PENDING, UsageStatus.PROCESSING]:
                return {
                    "status": 400,
                    "success": False,
                    "message": f"Cannot cancel generation. Current status: {usage_detail.status.value}",
                    "data": {
                        "current_status": usage_detail.status.value,
                        "cancellable_statuses": ["pending", "processing"]
                    }
                }
            
            # Update status to cancelled
            await self.update_usage_record(
                usage_id=usage_id,
                response_data={
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "cancellation_reason": "User requested cancellation"
                },
                status=UsageStatus.CANCELLED,
                error_message="Generation cancelled by user"
            )
            
            # Determine credit refund
            credits_refunded = 0
            if usage_detail.status == UsageStatus.PENDING:
                # Full refund for pending generations
                credits_refunded = usage_detail.credits_used
            elif usage_detail.status == UsageStatus.PROCESSING and usage_detail.started_at:
                # Partial refund based on time elapsed
                elapsed_minutes = (datetime.utcnow() - usage_detail.started_at).total_seconds() / 60
                if elapsed_minutes < 5:  # If less than 5 minutes processing, partial refund
                    credits_refunded = usage_detail.credits_used // 2
            
            # Process refund if applicable
            if credits_refunded > 0:
                users_collection = await MongoDB.get_collection("users")
                user_query = self._get_user_query(current_user)
                await users_collection.update_one(
                    user_query,
                    {"$inc": {"credits": credits_refunded}}
                )
            
            return {
                "status": 200,
                "success": True,
                "message": "Book generation cancelled successfully",
                "data": {
                    "usage_id": usage_id,
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "credits_refunded": credits_refunded,
                    "refund_policy": {
                        "pending": "Full refund",
                        "processing_under_5min": "50% refund", 
                        "processing_over_5min": "No refund"
                    }
                }
            }
            
        except ValueError as e:
            return {
                "status": 404,
                "success": False,
                "message": str(e),
                "data": {}
            }
        except Exception as e:
            logger.error(f"Error cancelling generation: {str(e)}")
            return {
                "status": 500,
                "success": False,
                "message": f"Failed to cancel generation: {str(e)}",
                "data": {}
            }

    async def get_user_book_history(self, current_user: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Get user's book generation history"""
        try:
            history_data = await self.usage_controller.get_user_usage_history(
                user_id=current_user,
                ai_model_slug="long-form-book",
                limit=limit,
                offset=offset
            )
            
            # Enhance history data with book-specific information
            enhanced_books = []
            for book in history_data["usage_history"]:
                enhanced_book = {
                    "usage_id": book.uid,
                    "book_title": "Unknown Title",
                    "status": book.status.value,
                    "credits_used": book.credits_used,
                    "created_at": book.created_at,
                    "completed_at": book.completed_at,
                    "has_pdf": False,
                    "word_count": 0,
                    "image_count": 0
                }
                
                # Extract book metadata if available
                if hasattr(book, 'metadata') and book.metadata:
                    book_meta = book.metadata.get("book_metadata", {})
                    enhanced_book.update({
                        "book_title": book_meta.get("title", "Unknown Title"),
                        "author": book_meta.get("author", "AI Generated"),
                        "genre": book_meta.get("genre", ""),
                        "word_count": book_meta.get("total_words", 0),
                        "image_count": book_meta.get("total_images", 0)
                    })
                
                # Check if PDF is available
                if hasattr(book, 'output_data') and book.output_data:
                    enhanced_book["has_pdf"] = bool(book.output_data.get("pdf_base64"))
                
                enhanced_books.append(enhanced_book)
            
            return {
                "status": 200,
                "success": True,
                "message": "Book generation history retrieved successfully",
                "data": {
                    "books": enhanced_books,
                    "pagination": history_data["pagination"],
                    "summary": {
                        "total_books": history_data["pagination"]["total"],
                        "completed_books": len([b for b in enhanced_books if b["status"] == "completed"]),
                        "total_words": sum(b["word_count"] for b in enhanced_books),
                        "total_credits_used": sum(b["credits_used"] for b in enhanced_books)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting book history: {str(e)}")
            return {
                "status": 500,
                "success": False,
                "message": f"Failed to retrieve book history: {str(e)}",
                "data": {}
            }

    async def duplicate_book(self, usage_id: str, current_user: str) -> Dict[str, Any]:
        """Duplicate a previous book generation with same settings"""
        try:
            # Get original book details
            usage_detail = await self.usage_controller.get_usage_detail(usage_id, current_user)
            
            if not usage_detail.input_data:
                return {
                    "status": 404,
                    "success": False,
                    "message": "Original book settings not found",
                    "data": {}
                }
            
            # Check user credits
            credit_info = await self.check_credits(current_user)
            if not credit_info["data"]["has_sufficient_credits"]:
                return {
                    "status": 400,
                    "success": False,
                    "message": "Insufficient credits to duplicate book",
                    "data": {
                        "credits_needed": credit_info["data"]["credits_needed"],
                        "credits_available": credit_info["data"]["user_credits"]
                    }
                }
            
            # Use original settings for new generation
            original_settings = usage_detail.input_data
            
            return {
                "status": 200,
                "success": True,
                "message": "Book settings retrieved for duplication",
                "data": {
                    "original_usage_id": usage_id,
                    "settings": original_settings,
                    "note": "Use these settings with the generate-stream endpoint to create a duplicate book",
                    "duplicate_endpoint": "/api/ai/long-form-book/generate-stream"
                }
            }
            
        except ValueError as e:
            return {
                "status": 404,
                "success": False,
                "message": str(e),
                "data": {}
            }
        except Exception as e:
            logger.error(f"Error duplicating book: {str(e)}")
            return {
                "status": 500,
                "success": False,
                "message": f"Failed to duplicate book: {str(e)}",
                "data": {}
            }

    # Legacy method for backward compatibility
    async def process_request(self, request_data: Dict[str, Any], current_user: str) -> Dict[str, Any]:
        """Legacy method for backward compatibility - redirects to streaming"""
        return {
            "status": 200,
            "success": True,
            "message": "Please use the streaming endpoint for book generation",
            "data": {
                "streaming_endpoint": "/api/ai/long-form-book/generate-stream",
                "note": "This provides real-time updates and better user experience",
                "migration_info": {
                    "old_endpoint": "/api/ai/long-form-book/generate",
                    "new_endpoint": "/api/ai/long-form-book/generate-stream",
                    "content_type": "text/event-stream",
                    "benefits": [
                        "Real-time progress updates",
                        "Better error handling", 
                        "Streaming content preview",
                        "Server-Sent Events (SSE) support",
                        "Improved user experience"
                    ]
                }
            }
        }

    # Legacy method for backward compatibility
    async def get_full_book_content(self, usage_id: str, current_user: str) -> Dict[str, Any]:
        """Legacy method - redirects to stored book endpoint"""
        result = await self.get_stored_book(usage_id, current_user)
        
        # Add migration note
        if result["success"]:
            result["data"]["migration_note"] = "This endpoint is deprecated. Use /api/ai/long-form-book/{usage_id}/stored instead."
        
        return result
