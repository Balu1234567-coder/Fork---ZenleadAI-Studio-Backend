from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UsageStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AIUsageHistory(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    uid: Optional[str] = Field(None, alias="_id")
    user_id: str
    ai_model_id: str
    ai_model_slug: str
    ai_model_name: str
    
    # Flexible settings storage - each model can have different settings
    model_settings: Dict[str, Any] = {}
    
    # Standard fields
    credits_used: int = 0
    credits_deducted: bool = False
    
    # Processing info
    status: UsageStatus = UsageStatus.PENDING
    
    # Input/Output data
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}  # This will store complete book data including PDF
    
    # Metadata for optimization
    metadata: Dict[str, Any] = {}
    
    # Error handling
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = {}
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UsageHistoryCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    ai_model_slug: str
    model_settings: Dict[str, Any]
    input_data: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class UsageHistoryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    uid: str = Field(alias="_id")
    ai_model_name: str
    ai_model_slug: str
    model_settings: Dict[str, Any]
    status: UsageStatus
    credits_used: int
    created_at: datetime
    completed_at: Optional[datetime]
    has_output: bool = False
    metadata: Dict[str, Any] = {}

class UsageHistoryDetail(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    uid: str = Field(alias="_id")
    ai_model_name: str
    ai_model_slug: str
    model_settings: Dict[str, Any]
    status: UsageStatus
    credits_used: int
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]  # Complete book data with PDF
    metadata: Dict[str, Any]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
