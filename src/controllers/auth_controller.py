from fastapi import HTTPException, Depends
from src.models.user import User, UserCreate, UserResponse, GoogleUserCreate
from src.config.mongodb import MongoDB
from src.config.env import env_config
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from pydantic import BaseModel
from src.middleware.auth import get_current_user, oauth2_scheme
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
import httpx

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize OAuth
oauth = OAuth()

if env_config.GOOGLE_CLIENT_ID and env_config.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=env_config.GOOGLE_CLIENT_ID,
        client_secret=env_config.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid_connect_configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

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
            if not user:
                raise HTTPException(status_code=401, detail="Invalid email or password")

            # Check if user has a password (local auth) or is Google OAuth user
            if user.get("auth_provider") == "google" and not user.get("password"):
                raise HTTPException(status_code=401, detail="Please use Google login for this account")

            if not user.get("password") or not pwd_context.verify(password, user["password"]):
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

    @staticmethod
    async def google_login(request: Request):
        """Initiate Google OAuth login"""
        try:
            if not env_config.GOOGLE_CLIENT_ID:
                raise HTTPException(status_code=500, detail="Google OAuth not configured")

            redirect_uri = env_config.GOOGLE_REDIRECT_URI
            return await oauth.google.authorize_redirect(request, redirect_uri)
        except Exception as e:
            print(f"Google login error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Google OAuth failed: {str(e)}")

    @staticmethod
    async def google_callback(request: Request) -> AuthResponse:
        """Handle Google OAuth callback"""
        try:
            if not env_config.GOOGLE_CLIENT_ID:
                raise HTTPException(status_code=500, detail="Google OAuth not configured")

            # Get the token from Google
            token = await oauth.google.authorize_access_token(request)
            user_info = token.get('userinfo')

            if not user_info:
                raise HTTPException(status_code=400, detail="Failed to get user info from Google")

            collection = await MongoDB.get_collection("users")

            # Check if user exists by Google ID or email
            existing_user = await collection.find_one({
                "$or": [
                    {"google_id": user_info['sub']},
                    {"email": user_info['email']}
                ]
            })

            if existing_user:
                # Update existing user with Google info if needed
                if not existing_user.get('google_id'):
                    await collection.update_one(
                        {"_id": existing_user["_id"]},
                        {
                            "$set": {
                                "google_id": user_info['sub'],
                                "profile_picture": user_info.get('picture'),
                                "auth_provider": "google"
                            }
                        }
                    )
                    existing_user.update({
                        "google_id": user_info['sub'],
                        "profile_picture": user_info.get('picture'),
                        "auth_provider": "google"
                    })

                user_dict = existing_user.copy()
                user_dict["_id"] = str(existing_user["_id"])
            else:
                # Create new user
                user_data = {
                    "firstName": user_info.get('given_name', ''),
                    "lastName": user_info.get('family_name', ''),
                    "email": user_info['email'],
                    "google_id": user_info['sub'],
                    "profile_picture": user_info.get('picture'),
                    "auth_provider": "google",
                    "credits": 150.0,
                    "created_at": datetime.utcnow()
                }

                result = await collection.insert_one(user_data)
                user_data["_id"] = str(result.inserted_id)
                user_dict = user_data

            # Generate JWT token
            token_data = {
                "sub": user_dict["_id"],
                "email": user_dict["email"],
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            token = jwt.encode(token_data, env_config.JWT_SECRET_KEY, algorithm=env_config.JWT_ALGORITHM)

            return AuthResponse(
                status=200,
                success=True,
                message="Google login successful",
                data=AuthData(
                    user=UserResponse(**user_dict),
                    access_token=token,
                    token_type="bearer"
                )
            )

        except Exception as e:
            print(f"Google callback error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Google OAuth callback failed: {str(e)}")

    @staticmethod
    async def google_user_info(access_token: str):
        """Get user info from Google using access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Google user info error: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
