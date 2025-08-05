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

class GoogleAuthUrlResponse(BaseModel):
    status: int
    success: bool
    auth_url: str
    state: str

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

    @staticmethod
    async def google_auth_url() -> GoogleAuthUrlResponse:
        """Generate Google OAuth authorization URL"""
        try:
            # Generate a random state parameter for CSRF protection
            state = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')

            # Google OAuth 2.0 authorization endpoint
            auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"

            params = {
                "client_id": env_config.GOOGLE_CLIENT_ID,
                "redirect_uri": env_config.GOOGLE_REDIRECT_URI,
                "scope": "openid email profile",
                "response_type": "code",
                "state": state,
                "access_type": "offline",
                "prompt": "consent"
            }

            auth_url = f"{auth_base_url}?{urllib.parse.urlencode(params)}"

            return GoogleAuthUrlResponse(
                status=200,
                success=True,
                auth_url=auth_url,
                state=state
            )
        except Exception as e:
            print(f"Google auth URL error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate Google auth URL: {str(e)}")

    @staticmethod
    async def google_callback(code: str, state: str) -> AuthResponse:
        """Handle Google OAuth callback and create/login user"""
        try:
            # Exchange authorization code for access token
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": env_config.GOOGLE_CLIENT_ID,
                "client_secret": env_config.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": env_config.GOOGLE_REDIRECT_URI,
            }

            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_data)
                token_response.raise_for_status()
                token_json = token_response.json()

                # Get user info from Google
                userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                headers = {"Authorization": f"Bearer {token_json['access_token']}"}
                userinfo_response = await client.get(userinfo_url, headers=headers)
                userinfo_response.raise_for_status()
                user_info = userinfo_response.json()

            # Extract user information
            google_id = user_info["id"]
            email = user_info["email"]
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            profile_picture = user_info.get("picture")

            collection = await MongoDB.get_collection("users")

            # Check if user exists by Google ID or email
            existing_user = await collection.find_one({
                "$or": [
                    {"google_id": google_id},
                    {"email": email}
                ]
            })

            if existing_user:
                # Update existing user with Google info if needed
                if not existing_user.get("google_id"):
                    await collection.update_one(
                        {"_id": existing_user["_id"]},
                        {
                            "$set": {
                                "google_id": google_id,
                                "profile_picture": profile_picture,
                                "auth_provider": "google"
                            }
                        }
                    )
                    existing_user.update({
                        "google_id": google_id,
                        "profile_picture": profile_picture,
                        "auth_provider": "google"
                    })

                user_dict = existing_user.copy()
                user_dict["_id"] = str(existing_user["_id"])
            else:
                # Create new user
                google_user_data = {
                    "firstName": first_name,
                    "lastName": last_name,
                    "email": email,
                    "google_id": google_id,
                    "profile_picture": profile_picture,
                    "auth_provider": "google",
                    "credits": 150.0,
                    "created_at": datetime.utcnow()
                }

                result = await collection.insert_one(google_user_data)
                user_dict = google_user_data.copy()
                user_dict["_id"] = str(result.inserted_id)

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
                message="Google authentication successful",
                data=AuthData(
                    user=UserResponse(**user_dict),
                    access_token=token,
                    token_type="bearer"
                )
            )

        except Exception as e:
            print(f"Google callback error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Google authentication failed: {str(e)}")
