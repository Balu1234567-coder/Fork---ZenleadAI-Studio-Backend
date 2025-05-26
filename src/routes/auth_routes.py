from fastapi import APIRouter
from src.models.user import UserCreate
from src.controllers.auth_controller import AuthController, AuthResponse
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=AuthResponse)
async def register(user: UserCreate):
    return await AuthController.register(user)

@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    return await AuthController.login(login_data.email, login_data.password)