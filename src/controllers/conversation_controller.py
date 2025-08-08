from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse
from src.models.conversation import (
    Conversation, ConversationRequest, ConversationMessage, 
    ConversationResponse, ConversationCategory
)
from src.config.mongodb import MongoDB
from src.middleware.auth import get_current_user
from src.services.ai_service import AIService
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from typing import List, Optional
import json
from datetime import datetime

class ConversationListResponse(BaseModel):
    status: int
    success: bool
    message: str
    data: List[ConversationResponse]

class ConversationDetailResponse(BaseModel):
    status: int
    success: bool
    message: str
    data: Conversation

class ConversationController:
    def __init__(self):
        self.ai_service = AIService()

    @staticmethod
    def _prepare_conversation_data(conversation_doc: dict) -> dict:
        """Prepare conversation data by converting ObjectId to string"""
        if "_id" in conversation_doc:
            conversation_doc["_id"] = str(conversation_doc["_id"])
        return conversation_doc

    async def create_conversation_stream(
        self, 
        request: ConversationRequest, 
        current_user: str = Depends(get_current_user)
    ):
        """Create new conversation with streaming response"""
        try:
            # Detect category if not provided
            category = request.category or self.ai_service.detect_category(request.message)
            
            # Create new conversation in database
            collection = await MongoDB.get_collection("conversations")
            
            conversation_data = {
                "user_id": current_user,
                "title": None,  # Will be generated after first response
                "messages": [
                    {
                        "role": "user",
                        "content": request.message,
                        "timestamp": datetime.utcnow()
                    }
                ],
                "category": category.value,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.insert_one(conversation_data)
            conversation_id = str(result.inserted_id)
            
            async def generate_stream():
                try:
                    # Send initial metadata
                    yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conversation_id, 'category': category.value})}\n\n"
                    
                    full_response = ""
                    
                    # Generate AI response
                    async for chunk in self.ai_service.generate_response_stream(
                        request.message, category
                    ):
                        full_response += chunk
                        # Send chunk to client
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    
                    # Save AI response to database
                    ai_message = {
                        "role": "assistant",
                        "content": full_response,
                        "timestamp": datetime.utcnow()
                    }
                    
                    # Generate title for conversation
                    title = await self.ai_service.generate_conversation_title(request.message)
                    
                    await collection.update_one(
                        {"_id": ObjectId(conversation_id)},
                        {
                            "$push": {"messages": ai_message},
                            "$set": {
                                "title": title,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    # Send completion signal
                    yield f"data: {json.dumps({'type': 'complete', 'title': title})}\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def continue_conversation_stream(
        self,
        conversation_id: str,
        request: ConversationRequest,
        current_user: str = Depends(get_current_user)
    ):
        """Continue existing conversation with streaming response"""
        try:
            conversation_obj_id = ObjectId(conversation_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        collection = await MongoDB.get_collection("conversations")
        conversation = await collection.find_one({
            "_id": conversation_obj_id,
            "user_id": current_user
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Detect category if not provided (or use existing category)
        category = request.category or ConversationCategory(conversation.get("category", "general_chat"))
        
        async def generate_stream():
            try:
                # Add user message to conversation
                user_message = {
                    "role": "user",
                    "content": request.message,
                    "timestamp": datetime.utcnow()
                }
                
                await collection.update_one(
                    {"_id": conversation_obj_id},
                    {
                        "$push": {"messages": user_message},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                
                # Send initial metadata
                yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conversation_id, 'category': category.value})}\n\n"
                
                full_response = ""
                conversation_history = conversation.get("messages", [])
                
                # Generate AI response with conversation context
                async for chunk in self.ai_service.generate_response_stream(
                    request.message, category, conversation_history
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # Save AI response
                ai_message = {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.utcnow()
                }
                
                await collection.update_one(
                    {"_id": conversation_obj_id},
                    {
                        "$push": {"messages": ai_message},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

    async def get_conversations(
        self,
        current_user: str = Depends(get_current_user),
        limit: int = 20,
        offset: int = 0
    ) -> ConversationListResponse:
        """Get user's conversations"""
        collection = await MongoDB.get_collection("conversations")
        
        cursor = collection.find(
            {"user_id": current_user}
        ).sort("updated_at", -1).skip(offset).limit(limit)
        
        conversations = []
        async for conv in cursor:
            # Convert ObjectId to string
            conv = self._prepare_conversation_data(conv)
            messages = conv.get("messages", [])
            
            conversations.append(ConversationResponse(
                _id=conv["_id"],  # Now it's a string
                user_id=conv["user_id"],
                title=conv.get("title"),
                category=conv.get("category"),
                message_count=len(messages),
                last_message=messages[-1]["content"] if messages else None,
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            ))
        
        return ConversationListResponse(
            status=200,
            success=True,
            message="Conversations retrieved successfully",
            data=conversations
        )

    async def get_conversation(
        self,
        conversation_id: str,
        current_user: str = Depends(get_current_user)
    ) -> ConversationDetailResponse:
        """Get specific conversation details"""
        try:
            conversation_obj_id = ObjectId(conversation_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        collection = await MongoDB.get_collection("conversations")
        conversation = await collection.find_one({
            "_id": conversation_obj_id,
            "user_id": current_user
        })
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Convert ObjectId to string
        conversation = self._prepare_conversation_data(conversation)
        
        return ConversationDetailResponse(
            status=200,
            success=True,
            message="Conversation retrieved successfully",
            data=Conversation(**conversation)
        )

    async def delete_conversation(
        self,
        conversation_id: str,
        current_user: str = Depends(get_current_user)
    ):
        """Delete a conversation"""
        try:
            conversation_obj_id = ObjectId(conversation_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        collection = await MongoDB.get_collection("conversations")
        result = await collection.delete_one({
            "_id": conversation_obj_id,
            "user_id": current_user
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "status": 200,
            "success": True,
            "message": "Conversation deleted successfully"
        }

    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str,
        current_user: str = Depends(get_current_user)
    ):
        """Update conversation title"""
        try:
            conversation_obj_id = ObjectId(conversation_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
        collection = await MongoDB.get_collection("conversations")
        result = await collection.update_one(
            {"_id": conversation_obj_id, "user_id": current_user},
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "status": 200,
            "success": True,
            "message": "Conversation title updated successfully"
        }
