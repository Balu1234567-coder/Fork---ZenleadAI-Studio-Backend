from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from src.controllers.ai_models.long_form_book_controller import LongFormBookController
from src.middleware.auth import get_current_user

router = APIRouter()
controller = LongFormBookController()

@router.post(
    "/long-form-book/generate-stream",
    summary="Generate Long-form Book with Server-Sent Events",
    description="Generate a comprehensive book with real-time streaming updates using SSE"
)
async def generate_long_form_book_stream(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user)
) -> StreamingResponse:
    """
    Generate a complete long-form book with Server-Sent Events streaming.
    
    **Features:**
    - Real-time progress updates via SSE
    - Chapter-by-chapter streaming with images
    - Complete book storage in database
    - PDF generation with images
    - Live status updates
    
    **Response Format:** Server-Sent Events (text/event-stream)
    Event types:
    - `start`: Generation started
    - `progress`: Progress updates with percentage
    - `structure`: Book structure generated
    - `chapter_complete`: Chapter finished with preview
    - `image_added`: Image added to chapter
    - `complete`: Generation completed with full data
    - `stored`: Book stored in database
    - `credits_deducted`: Credits processed
    - `error`: Error occurred with error codes
    
    **Credits Required**: 50 credits
    **Estimated Time**: 15-30 minutes with images
    """
    try:
        return await controller.process_request_stream(request, current_user)
    except Exception as e:
        # Return SSE error format instead of JSON
        async def error_stream():
            error_data = {
                "type": "error",
                "error_code": "STARTUP_ERROR",
                "message": f"Failed to start book generation: {str(e)}",
                "timestamp": str(datetime.utcnow())
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

@router.get(
    "/long-form-book/check-credits",
    response_model=Dict[str, Any],
    summary="Check User Credits for Book Generation",
    description="Pre-flight check to verify sufficient credits before starting generation"
)
async def check_user_credits(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if user has sufficient credits to generate a book.
    
    **Returns:**
    - user_credits: Current available credits
    - credits_required: Credits needed (50)
    - has_sufficient_credits: Boolean if user can proceed
    - credits_needed: Additional credits required (if any)
    """
    try:
        result = await controller.check_credits(current_user)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check credits: {str(e)}")

@router.get(
    "/long-form-book/{usage_id}/stored",
    response_model=Dict[str, Any],
    summary="Get Complete Stored Book with Images",
    description="Retrieve complete stored book data including all chapters, images, and PDF"
)
async def get_stored_book(
    usage_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get complete stored book data including:
    - Full book content with all chapters
    - All generated images
    - Complete PDF in base64 format
    - Book metadata and statistics
    - Generation information
    """
    try:
        result = await controller.get_stored_book(usage_id, current_user)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stored book: {str(e)}")

@router.get(
    "/long-form-book/{usage_id}/pdf",
    response_model=Dict[str, Any],
    summary="Download Book PDF",
    description="Get the generated PDF with images for download"
)
async def get_book_pdf(
    usage_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Download the complete book PDF with images.
    
    **Frontend Usage:**
    ```
    const response = await fetch('/api/ai/long-form-book/{usage_id}/pdf');
    const data = await response.json();
    
    // Create download
    const link = document.createElement('a');
    link.href = `data:application/pdf;base64,${data.data.pdf_base64}`;
    link.download = data.data.filename;
    link.click();
    ```
    """
    try:
        result = await controller.get_book_pdf(usage_id, current_user)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve PDF: {str(e)}")

@router.get(
    "/long-form-book/{usage_id}/status",
    response_model=Dict[str, Any],
    summary="Get Generation Status",
    description="Check the current status of book generation with progress estimates"
)
async def get_generation_status(
    usage_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get real-time status of book generation including:
    - Current processing stage
    - Estimated completion time
    - Progress indicators
    - Error information if any
    """
    try:
        result = await controller.get_generation_status(usage_id, current_user)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post(
    "/long-form-book/{usage_id}/cancel",
    response_model=Dict[str, Any],
    summary="Cancel Book Generation",
    description="Cancel ongoing generation with credit refund policy"
)
async def cancel_generation(
    usage_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel ongoing book generation with smart refund policy:
    - Pending: Full refund (50 credits)
    - Processing <5min: 50% refund (25 credits)
    - Processing >5min: No refund
    """
    try:
        result = await controller.cancel_generation(usage_id, current_user)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel generation: {str(e)}")

@router.get(
    "/long-form-book/history",
    response_model=Dict[str, Any],
    summary="Get User's Book History",
    description="Get user's book generation history with enhanced metadata"
)
async def get_user_book_history(
    current_user: str = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get comprehensive book generation history including:
    - All generated books with titles and status
    - Word counts and image counts
    - Credit usage statistics
    - Download availability
    """
    try:
        result = await controller.get_user_book_history(current_user, limit, offset)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get(
    "/long-form-book/{usage_id}/duplicate",
    response_model=Dict[str, Any],
    summary="Get Settings for Book Duplication",
    description="Get original settings to create a duplicate book"
)
async def duplicate_book_settings(
    usage_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the original settings from a previous book generation
    to create a duplicate with the same parameters.
    """
    try:
        result = await controller.duplicate_book(usage_id, current_user)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get duplicate settings: {str(e)}")

# Legacy endpoints for backward compatibility
@router.post(
    "/long-form-book/generate",
    response_model=Dict[str, Any],
    summary="Generate Long-form Book (Legacy)",
    description="⚠️ Deprecated: Use /generate-stream for better experience"
)
async def generate_long_form_book_legacy(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    **⚠️ DEPRECATED ENDPOINT**
    
    This endpoint is deprecated. Please use:
    `/api/ai/long-form-book/generate-stream` 
    
    For real-time Server-Sent Events streaming with better user experience.
    """
    try:
        result = await controller.process_request(request, current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process request: {str(e)}")

@router.get(
    "/long-form-book/{usage_id}/content",
    response_model=Dict[str, Any],
    summary="Get Full Book Content (Legacy)",
    description="⚠️ Deprecated: Use /stored endpoint instead"
)
async def get_book_content_legacy(
    usage_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    **⚠️ DEPRECATED ENDPOINT**
    
    This endpoint is deprecated. Please use:
    `/api/ai/long-form-book/{usage_id}/stored`
    
    For complete book data including images and PDF.
    """
    try:
        result = await controller.get_full_book_content(usage_id, current_user)
        if not result["success"]:
            raise HTTPException(status_code=result["status"], detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve content: {str(e)}")

@router.get(
    "/long-form-book/settings",
    response_model=Dict[str, Any],
    summary="Get Book Generation Settings",
    description="Get comprehensive settings and API information"
)
async def get_book_settings() -> Dict[str, Any]:
    """
    Get all available settings, endpoints, and system information
    for book generation including SSE streaming details.
    """
    return {
        "status": 200,
        "success": True,
        "message": "Long-form Book Generation API Information",
        "data": {
            "primary_endpoint": "/api/ai/long-form-book/generate-stream",
            "content_type": "text/event-stream",
            "streaming_method": "Server-Sent Events (SSE)",
            "credits_required": 50,
            "estimated_time": "15-30 minutes",
            "features": [
                "Real-time progress updates",
                "Chapter-by-chapter generation",
                "Image search and integration",
                "PDF generation with images",
                "Complete database storage",
                "Credit management with refunds",
                "Generation status tracking"
            ],
            "endpoints": {
                "generate": "/api/ai/long-form-book/generate-stream",
                "check_credits": "/api/ai/long-form-book/check-credits",
                "get_stored": "/api/ai/long-form-book/{usage_id}/stored",
                "download_pdf": "/api/ai/long-form-book/{usage_id}/pdf",
                "get_status": "/api/ai/long-form-book/{usage_id}/status",
                "cancel": "/api/ai/long-form-book/{usage_id}/cancel",
                "history": "/api/ai/long-form-book/history",
                "duplicate": "/api/ai/long-form-book/{usage_id}/duplicate"
            },
            "sse_events": [
                "start", "progress", "structure", "chapter_complete", 
                "image_added", "complete", "stored", "credits_deducted", "error"
            ],
            "dynamic_settings": "/api/ai/models/long-form-book/settings",
            "integration_guide": {
                "frontend_example": "Use EventSource or fetch with streaming for SSE",
                "content_type": "text/event-stream",
                "event_format": "event: {type}\\ndata: {json_data}\\n\\n"
            }
        }
    }
    @router.get("/long-form-book/{usage_id}/chapter/{chapter_number}/full")
    async def get_full_chapter_content(
        usage_id: str,
        chapter_number: int,
        current_user: str = Depends(get_current_user)
    ):
        """Get full chapter content for display"""
        try:
            usage_detail = await controller.usage_controller.get_usage_detail(usage_id, current_user)
            
            if not usage_detail.output_data:
                raise HTTPException(status_code=404, detail="Book not found")
            
            complete_chapters = usage_detail.output_data.get("complete_chapters", [])
            
            for chapter in complete_chapters:
                if chapter["chapter_number"] == chapter_number:
                    return {
                        "status": 200,
                        "success": True,
                        "data": {
                            "chapter_number": chapter["chapter_number"],
                            "title": chapter["title"],
                            "full_content": chapter["full_content"],  # FULL CONTENT
                            "formatted_content": chapter.get("formatted_content", ""),
                            "word_count": chapter["word_count"],
                            "images": chapter.get("images", [])
                        }
                    }
            
            raise HTTPException(status_code=404, detail="Chapter not found")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
