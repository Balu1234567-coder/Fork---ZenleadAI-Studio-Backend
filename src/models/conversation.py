from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ConversationCategory(str, Enum):
    GENERAL_CHAT = "general_chat"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    CODE_ANALYSIS = "code_analysis"
    DATABASE_QUERIES = "database_queries"
    CALCULATIONS = "calculations"

class ConversationRequest(BaseModel):
    message: str
    category: Optional[ConversationCategory] = None

class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseModel):
    uid: str = Field(alias="_id")  # Made required and string type
    user_id: str
    title: Optional[str] = None
    messages: List[ConversationMessage] = []
    category: Optional[ConversationCategory] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConversationResponse(BaseModel):
    uid: str = Field(alias="_id")  # Made required and string type
    user_id: str
    title: Optional[str] = None
    category: Optional[ConversationCategory] = None
    message_count: int
    last_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
