from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class AIModelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"

class UsageStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AIModelCategory(str, Enum):
    AUDIO = "audio"
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DATA = "data"
    CONTENT = "content"

class AIModel(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    name: str
    slug: str
    category: AIModelCategory
    description: str
    success_rate: int = 95
    features: List[str] = []
    input_types: List[str] = []
    output_types: List[str] = []
    pricing: Dict[str, Any] = {}
    status: AIModelStatus = AIModelStatus.ACTIVE
    estimated_time: str = "2-5 minutes"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AIUsageHistory(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    user_id: str
    ai_model_id: str
    ai_model_name: str
    request_data: Dict[str, Any] = {}
    response_data: Dict[str, Any] = {}
    status: UsageStatus = UsageStatus.PENDING
    credits_used: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# Request/Response Models
class BaseAIRequest(BaseModel):
    pass

class BaseAIResponse(BaseModel):
    status: int
    success: bool
    message: str
    data: Dict[str, Any]
    usage_id: Optional[str] = None

class AIModelResponse(BaseModel):
    uid: str = Field(alias="_id")
    name: str
    slug: str
    category: AIModelCategory
    description: str
    success_rate: int
    features: List[str]
    input_types: List[str]
    output_types: List[str]
    pricing: Dict[str, Any]
    estimated_time: str
    status: AIModelStatus

class UsageHistoryResponse(BaseModel):
    uid: str = Field(alias="_id")
    ai_model_name: str
    status: UsageStatus
    credits_used: int
    created_at: datetime
    completed_at: Optional[datetime]
    has_output: bool = False
