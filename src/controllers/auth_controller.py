from fastapi import HTTPException, Depends
from fastapi.responses import RedirectResponse
from src.models.user import User, UserCreate, UserResponse, GoogleUserCreate
from src.config.mongodb import MongoDB
from src.config.env import env_config
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from pydantic import BaseModel
from src.middleware.auth import get_current_user, oauth2_scheme
import httpx
import urllib.parse
import secrets
import base64

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthData(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str

class AuthResponse(BaseModel):
    status: int
    success: bool
    message: str
    data: AuthData

class VerifyResponse(BaseModel):
    status: int
    success: bool
    message: str

class AuthController:
    @staticmethod
    async def register(user_data: UserCreate) -> AuthResponse:
        try:
            collection = await MongoDB.get_collection("users")  # Await get_collection
            if await collection.find_one({"email": user_data.email}):
                raise HTTPException(status_code=400, detail="User with this email already exists")
            
            hashed_password = pwd_context.hash(user_data.password)
            
            user_dict = user_data.dict()
            user_dict["password"] = hashed_password
            user_dict["credits"] = 150.0
            user_dict["created_at"] = datetime.utcnow()
            
            result = await collection.insert_one(user_dict)
            user_dict["_id"] = str(result.inserted_id)
            
            token_data = {
                "sub": user_dict["_id"],
                "email": user_dict["email"],
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            token = jwt.encode(token_data, env_config.JWT_SECRET_KEY, algorithm=env_config.JWT_ALGORITHM)
            
            return AuthResponse(
                status=201,
                success=True,
                message="User registered successfully",
                data=AuthData(
                    user=UserResponse(**user_dict),
                    access_token=token,
                    token_type="bearer"
                )
            )
        except Exception as e:
            print(f"Register error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    @staticmethod
    async def login(email: str, password: str) -> AuthResponse:
        try:
            print("Login attempt for email:", email)
            collection = await MongoDB.get_collection("users")  # Await get_collection
            print("Collection accessed")
            user = await collection.find_one({"email": email})
            print("User query result:", user)
            if not user or not pwd_context.verify(password, user["password"]):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            print("Password verified")
            
            token_data = {
                "sub": str(user["_id"]),
                "email": user["email"],
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            print("Token data:", token_data)
            token = jwt.encode(token_data, env_config.JWT_SECRET_KEY, algorithm=env_config.JWT_ALGORITHM)
            print("JWT generated")
            
            user_dict = user.copy()
            user_dict["_id"] = str(user["_id"])
            print("User dict:", user_dict)
            
            return AuthResponse(
                status=200,
                success=True,
                message="Login successful",
                data=AuthData(
                    user=UserResponse(**user_dict),
                    access_token=token,
                    token_type="bearer"
                )
            )
        except Exception as e:
            print(f"Login error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

    @staticmethod
    async def verify_token(token: str = Depends(oauth2_scheme)) -> VerifyResponse:
        try:
            payload = jwt.decode(token, env_config.JWT_SECRET_KEY, algorithms=[env_config.JWT_ALGORITHM])
            uid: str = payload.get("sub")
            if not uid:
                raise HTTPException(status_code=401, detail="Invalid token")
            return VerifyResponse(
                status=200,
                success=True,
                message="Token is valid"
            )
        except JWTError as e:
            print(f"Verify token error: {str(e)}")
            return VerifyResponse(
                status=401,
                success=False,
                message=f"Invalid or expired token: {str(e)}"
            )
