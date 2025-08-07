from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    firstName: str
    lastName: str
    email: EmailStr
    password: Optional[str] = None  # Make password optional for Google users
    credits: float = 150.0
    created_at: datetime = datetime.utcnow()
    auth_provider: str = "local"  # "local" or "google"
    google_id: Optional[str] = None  # Store Google user ID

class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str

class GoogleUserCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    google_id: str

class UserResponse(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    firstName: str
    lastName: str
    email: EmailStr
    credits: float
    auth_provider: str

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
