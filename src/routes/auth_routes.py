from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse
from src.models.user import UserCreate
from src.controllers.auth_controller import AuthController, AuthResponse
from src.controllers.google_auth_controller import GoogleAuthController
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthUrlResponse(BaseModel):
    status: int
    success: bool
    message: str
    auth_url: str

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse)
async def register(user: UserCreate):
    return await AuthController.register(user)

@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    return await AuthController.login(login_data.email, login_data.password)

@router.get("/google", response_model=GoogleAuthUrlResponse)
async def google_auth():
    """Get Google OAuth URL for frontend to redirect to"""
    auth_url = GoogleAuthController.get_google_auth_url()
    return GoogleAuthUrlResponse(
        status=200,
        success=True,
        message="Google OAuth URL generated",
        auth_url=auth_url
    )

@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(None, description="State parameter")
):
    """Handle Google OAuth callback"""
    return await GoogleAuthController.google_callback(code)
