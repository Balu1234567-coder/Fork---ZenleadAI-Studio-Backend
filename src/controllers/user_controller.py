from fastapi import HTTPException, Depends
from src.models.user import UserResponse, UserUpdate
from src.config.mongodb import MongoDB
from src.middleware.auth import get_current_user
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId

class UserResponseData(BaseModel):
    user: UserResponse

class UserResponseModel(BaseModel):
    status: int
    success: bool
    message: str
    data: UserResponseData

class CreditsResponseData(BaseModel):
    credits: float

class CreditsResponseModel(BaseModel):
    status: int
    success: bool
    message: str
    data: CreditsResponseData

class UserController:
    @staticmethod
    def _prepare_user_data(user_doc: dict) -> dict:
        """Prepare user data with backward compatibility and proper _id conversion"""
        # Convert ObjectId to string
        if "_id" in user_doc and isinstance(user_doc["_id"], ObjectId):
            user_doc["_id"] = str(user_doc["_id"])
        
        # Handle backward compatibility for auth_provider
        if "auth_provider" not in user_doc:
            user_doc["auth_provider"] = "local"
        
        # Handle backward compatibility for google_id
        if "google_id" not in user_doc:
            user_doc["google_id"] = None
            
        return user_doc

    @staticmethod
    async def get_user(userId: str, current_user: str = Depends(get_current_user)) -> UserResponseModel:
        # Optional: Restrict to own user data
        if userId != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this user")
        
        try:
            userId_obj = ObjectId(userId)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        collection = await MongoDB.get_collection("users")
        user = await collection.find_one({"_id": userId_obj})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare user data with backward compatibility and _id conversion
        user = UserController._prepare_user_data(user)
        
        return UserResponseModel(
            status=200,
            success=True,
            message="User data retrieved successfully",
            data=UserResponseData(user=UserResponse(**user))
        )

    @staticmethod
    async def update_user(userId: str, user_data: UserUpdate, current_user: str = Depends(get_current_user)) -> UserResponseModel:
        # Optional: Restrict to own user data
        if userId != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
        try:
            userId_obj = ObjectId(userId)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        collection = await MongoDB.get_collection("users")
        user = await collection.find_one({"_id": userId_obj})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check email uniqueness if email is being updated
        if user_data.email and user_data.email != user["email"]:
            if await collection.find_one({"email": user_data.email}):
                raise HTTPException(status_code=400, detail="Email already in use")
        
        # Prepare update data
        update_data = user_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        
        # Update user in MongoDB
        await collection.update_one({"_id": userId_obj}, {"$set": update_data})
        
        # Fetch updated user
        updated_user = await collection.find_one({"_id": userId_obj})
        updated_user = UserController._prepare_user_data(updated_user)
        
        return UserResponseModel(
            status=200,
            success=True,
            message="User data updated successfully",
            data=UserResponseData(user=UserResponse(**updated_user))
        )

    @staticmethod
    async def get_user_credits(userId: str, current_user: str = Depends(get_current_user)) -> CreditsResponseModel:
        # Restrict to own user data
        if userId != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this user's credits")
        
        try:
            userId_obj = ObjectId(userId)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        collection = await MongoDB.get_collection("users")
        user = await collection.find_one({"_id": userId_obj}, {"credits": 1})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return CreditsResponseModel(
            status=200,
            success=True,
            message="User credits retrieved successfully",
            data=CreditsResponseData(credits=user["credits"])
        )
