from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    firstName: str
    lastName: str
    email: EmailStr
    password: Optional[str] = None  # Optional for Google OAuth users
    google_id: Optional[str] = None  # Google user ID
    profile_picture: Optional[str] = None  # Google profile picture URL
    auth_provider: str = "local"  # "local" or "google"
    credits: float = 150.0
    created_at: datetime = datetime.utcnow()

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
    profile_picture: Optional[str] = None

class UserResponse(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    firstName: str
    lastName: str
    email: EmailStr
    credits: float
    profile_picture: Optional[str] = None
    auth_provider: str

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
