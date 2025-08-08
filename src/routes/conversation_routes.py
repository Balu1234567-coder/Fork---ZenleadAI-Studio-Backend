from fastapi import APIRouter, Depends, Query
from src.controllers.conversation_controller import ConversationController
from src.models.conversation import ConversationRequest
from src.middleware.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/conversation", tags=["Conversation"])
controller = ConversationController()

class UpdateTitleRequest(BaseModel):
    title: str

@router.post("/new")
async def create_conversation(
    request: ConversationRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new conversation with streaming response"""
    return await controller.create_conversation_stream(request, current_user)

@router.post("/{conversation_id}/message")
async def continue_conversation(
    conversation_id: str,
    request: ConversationRequest,
    current_user: str = Depends(get_current_user)
):
    """Continue existing conversation with streaming response"""
    return await controller.continue_conversation_stream(conversation_id, request, current_user)

@router.get("/")
async def get_conversations(
    current_user: str = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get user's conversations"""
    return await controller.get_conversations(current_user, limit, offset)

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get specific conversation details"""
    return await controller.get_conversation(conversation_id, current_user)

@router.put("/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    request: UpdateTitleRequest,
    current_user: str = Depends(get_current_user)
):
    """Update conversation title"""
    return await controller.update_conversation_title(conversation_id, request.title, current_user)

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a conversation"""
    return await controller.delete_conversation(conversation_id, current_user)
