from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    uid: Optional[str] = Field(None, alias="_id")
    firstName: str
    lastName: str
    email: EmailStr
    password: Optional[str] = None  # Optional for Google OAuth users
    credits: float = 150.0
    created_at: datetime = datetime.utcnow()
    # Google OAuth fields
    google_id: Optional[str] = None
    profile_picture: Optional[str] = None
    auth_provider: str = "local"  # "local" or "google"

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

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
