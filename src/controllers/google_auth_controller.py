from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
import urllib.parse
from src.models.user import UserResponse
from src.controllers.auth_controller import AuthData, AuthResponse
from src.config.mongodb import MongoDB
from src.config.env import env_config
from datetime import datetime, timedelta
from jose import jwt
import logging
import json
import base64

logger = logging.getLogger(__name__)

class GoogleAuthController:
    # Google OAuth credentials - make sure these match your Google Console settings
    GOOGLE_CLIENT_ID = env_config.GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET = env_config.GOOGLE_CLIENT_SECRET 
    GOOGLE_REDIRECT_URI = env_config.GOOGLE_REDIRECT_URI  # This MUST match Google Console
    
    @staticmethod
    def get_google_auth_url() -> str:
        """Generate Google OAuth URL for frontend to redirect to"""
        base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "client_id": GoogleAuthController.GOOGLE_CLIENT_ID,
            "redirect_uri": GoogleAuthController.GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "state": "random_state_string"  # Add state for security
        }
        
        url = f"{base_url}?" + urllib.parse.urlencode(params)
        return url
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> dict:
        """Exchange authorization code for access token"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": GoogleAuthController.GOOGLE_CLIENT_ID,
            "client_secret": GoogleAuthController.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GoogleAuthController.GOOGLE_REDIRECT_URI,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                logger.info(f"Token exchange response status: {response.status_code}")
                logger.info(f"Token exchange response: {response.text}")
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to exchange code for token: {response.text}")
                
                return response.json()
        except Exception as e:
            logger.error(f"Token exchange error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> dict:
        """Get user information from Google using access token"""
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(user_info_url, headers=headers)
                logger.info(f"User info response status: {response.status_code}")
                
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Failed to get user info from Google")
                
                return response.json()
        except Exception as e:
            logger.error(f"Get user info error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")
    
    @staticmethod
    def _prepare_user_data(user_doc: dict) -> dict:
        """Prepare user data with backward compatibility"""
        user_doc["_id"] = str(user_doc["_id"])
        
        # Handle backward compatibility
        if "auth_provider" not in user_doc:
            user_doc["auth_provider"] = "local"
        if "google_id" not in user_doc:
            user_doc["google_id"] = None
            
        return user_doc
    
    @staticmethod
    async def google_callback(code: str, frontend_url: str = env_config.FRONTEND_URI) -> RedirectResponse:
        """Handle Google OAuth callback"""
        try:
            logger.info(f"Processing Google callback with code: {code[:20]}...")
            
            # Exchange code for tokens
            token_data = await GoogleAuthController.exchange_code_for_token(code)
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(status_code=400, detail="No access token received")
            
            # Get user info from Google
            user_info = await GoogleAuthController.get_google_user_info(access_token)
            logger.info(f"Google user info received: {user_info.get('email')}")
            
            collection = await MongoDB.get_collection("users")
            
            # Check if user exists
            existing_user = await collection.find_one({
                "$or": [
                    {"email": user_info['email']},
                    {"google_id": user_info['id']}
                ]
            })
            
            if existing_user:
                logger.info(f"Existing user found: {existing_user.get('email')}")
                # Update existing user
                update_data = {}
                if existing_user.get('auth_provider') != 'google':
                    update_data['auth_provider'] = 'google'
                    update_data['google_id'] = user_info['id']
                
                if update_data:
                    await collection.update_one(
                        {"_id": existing_user["_id"]}, 
                        {"$set": update_data}
                    )
                    existing_user.update(update_data)
                
                user_dict = GoogleAuthController._prepare_user_data(existing_user.copy())
            else:
                logger.info(f"Creating new user: {user_info['email']}")
                # Create new user
                new_user = {
                    "firstName": user_info.get('given_name', ''),
                    "lastName": user_info.get('family_name', ''),
                    "email": user_info['email'],
                    "password": None,
                    "credits": 150.0,
                    "created_at": datetime.utcnow(),
                    "auth_provider": "google",
                    "google_id": user_info['id']
                }
                
                result = await collection.insert_one(new_user)
                new_user["_id"] = str(result.inserted_id)
                user_dict = GoogleAuthController._prepare_user_data(new_user)
            
            # Generate JWT token
            token_data = {
                "sub": user_dict["_id"],
                "email": user_dict["email"],
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            jwt_token = jwt.encode(token_data, env_config.JWT_SECRET_KEY, algorithm=env_config.JWT_ALGORITHM)
            
            # Create user response object with complete user data
            user_response = UserResponse(**user_dict)
            
            # Create complete auth data (same format as regular auth controller)
            auth_data = {
                "user": {
                    "uid": user_response.uid,
                    "firstName": user_response.firstName,
                    "lastName": user_response.lastName,
                    "email": user_response.email,
                    "credits": user_response.credits,
                    "auth_provider": user_response.auth_provider
                },
                "access_token": jwt_token,
                "token_type": "bearer"
            }
            
            # Convert to JSON and then to base64 to safely pass in URL
            auth_data_json = json.dumps(auth_data, default=str)
            auth_data_b64 = base64.urlsafe_b64encode(auth_data_json.encode()).decode()
            
            # Redirect to frontend with complete auth data
            redirect_url = f"{frontend_url}/auth/callback?auth_data={auth_data_b64}&success=true"
            logger.info(f"Redirecting to: {redirect_url}")
            logger.info(f"User data being sent: {auth_data['user']}")
            return RedirectResponse(url=redirect_url)
            
        except Exception as e:
            logger.error(f"Google callback error: {str(e)}")
            error_url = f"{frontend_url}/auth/callback?error={str(e)}&success=false"
            return RedirectResponse(url=error_url)

    @staticmethod
    async def google_auth_direct(id_token_str: str) -> AuthResponse:
        """Alternative endpoint for direct Google auth that returns structured data"""
        try:
            # This method can be used if you want a direct API endpoint instead of redirect
            # You would call this from frontend with Google ID token
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
            
            # Verify the ID token
            idinfo = id_token.verify_oauth2_token(
                id_token_str, google_requests.Request(), GoogleAuthController.GOOGLE_CLIENT_ID
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            user_info = {
                'id': idinfo['sub'],
                'email': idinfo['email'],
                'given_name': idinfo.get('given_name', ''),
                'family_name': idinfo.get('family_name', ''),
            }
            
            collection = await MongoDB.get_collection("users")
            
            # Check if user exists
            existing_user = await collection.find_one({
                "$or": [
                    {"email": user_info['email']},
                    {"google_id": user_info['id']}
                ]
            })
            
            if existing_user:
                # Update existing user
                update_data = {}
                if existing_user.get('auth_provider') != 'google':
                    update_data['auth_provider'] = 'google'
                    update_data['google_id'] = user_info['id']
                
                if update_data:
                    await collection.update_one(
                        {"_id": existing_user["_id"]}, 
                        {"$set": update_data}
                    )
                    existing_user.update(update_data)
                
                user_dict = GoogleAuthController._prepare_user_data(existing_user.copy())
            else:
                # Create new user
                new_user = {
                    "firstName": user_info.get('given_name', ''),
                    "lastName": user_info.get('family_name', ''),
                    "email": user_info['email'],
                    "password": None,
                    "credits": 150.0,
                    "created_at": datetime.utcnow(),
                    "auth_provider": "google",
                    "google_id": user_info['id']
                }
                
                result = await collection.insert_one(new_user)
                new_user["_id"] = str(result.inserted_id)
                user_dict = GoogleAuthController._prepare_user_data(new_user)
            
            # Generate JWT token
            token_data = {
                "sub": user_dict["_id"],
                "email": user_dict["email"],
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            jwt_token = jwt.encode(token_data, env_config.JWT_SECRET_KEY, algorithm=env_config.JWT_ALGORITHM)
            
            # Return structured response like regular auth
            return AuthResponse(
                status=200,
                success=True,
                message="Google authentication successful",
                data=AuthData(
                    user=UserResponse(**user_dict),
                    access_token=jwt_token,
                    token_type="bearer"
                )
            )
            
        except Exception as e:
            logger.error(f"Google direct auth error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Google authentication failed: {str(e)}")
