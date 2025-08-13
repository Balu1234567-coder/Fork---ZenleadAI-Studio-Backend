from abc import ABC, abstractmethod
from fastapi import HTTPException, Depends, UploadFile
from src.config.mongodb import MongoDB
from src.middleware.auth import get_current_user
from src.models.ai_models.base_ai_model import *
from bson import ObjectId
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAIController(ABC):
    def __init__(self, model_slug: str):
        self.model_slug = model_slug
        
    @staticmethod
    def _prepare_document_data(doc: dict) -> dict:
        """Convert ObjectId to string"""
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_ai_model_info(self) -> Dict[str, Any]:
        """Get AI model information"""
        try:
            models_collection = await MongoDB.get_collection("ai_models")
            model = await models_collection.find_one({"slug": self.model_slug})
            
            if not model:
                raise HTTPException(status_code=404, detail="AI Model not found")
            
            model = self._prepare_document_data(model)
            return {
                "status": 200,
                "success": True,
                "message": "AI Model info retrieved successfully",
                "data": AIModelResponse(**model)
            }
        except Exception as e:
            logger.error(f"Error getting AI model info: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_usage_record(
        self, 
        user_id: str, 
        request_data: Dict[str, Any],
        credits_required: int
    ) -> str:
        """Create usage history record"""
        try:
            # Get AI model info
            models_collection = await MongoDB.get_collection("ai_models")
            model = await models_collection.find_one({"slug": self.model_slug})
            
            if not model:
                raise HTTPException(status_code=404, detail="AI Model not found")
            
            # Check user credits
            users_collection = await MongoDB.get_collection("users")
            user_query = {"_id": ObjectId(user_id)} if len(user_id) == 24 else {"_id": user_id}
            user = await users_collection.find_one(user_query)
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if user["credits"] < credits_required:
                raise HTTPException(status_code=400, detail="Insufficient credits")
            
            # Create usage record
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            usage_data = {
                "user_id": user_id,
                "ai_model_id": str(model["_id"]),
                "ai_model_name": model["name"],
                "request_data": request_data,
                "response_data": {},
                "status": UsageStatus.PENDING.value,
                "credits_used": credits_required,
                "created_at": datetime.utcnow()
            }
            
            result = await usage_collection.insert_one(usage_data)
            
            # Deduct credits
            await users_collection.update_one(
                user_query,
                {"$inc": {"credits": -credits_required}}
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error creating usage record: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_usage_record(
        self,
        usage_id: str,
        response_data: Dict[str, Any],
        status: UsageStatus,
        error_message: Optional[str] = None
    ):
        """Update usage history record"""
        try:
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            
            update_data = {
                "response_data": response_data,
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
            
            if status == UsageStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow()
            
            if error_message:
                update_data["error_message"] = error_message
            
            await usage_collection.update_one(
                {"_id": ObjectId(usage_id)},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Error updating usage record: {str(e)}")

    async def get_user_usage_history(
        self,
        current_user: str = Depends(get_current_user),
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's usage history for this AI model"""
        try:
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            
            # Get AI model info first
            models_collection = await MongoDB.get_collection("ai_models")
            model = await models_collection.find_one({"slug": self.model_slug})
            
            if not model:
                raise HTTPException(status_code=404, detail="AI Model not found")
            
            cursor = usage_collection.find({
                "user_id": current_user,
                "ai_model_id": str(model["_id"])
            }).sort("created_at", -1).skip(offset).limit(limit)
            
            history = []
            async for usage in cursor:
                usage = self._prepare_document_data(usage)
                history.append(UsageHistoryResponse(
                    _id=usage["_id"],
                    ai_model_name=usage["ai_model_name"],
                    status=usage["status"],
                    credits_used=usage["credits_used"],
                    created_at=usage["created_at"],
                    completed_at=usage.get("completed_at"),
                    has_output=bool(usage.get("response_data", {}))
                ))
            
            return {
                "status": 200,
                "success": True,
                "message": "Usage history retrieved successfully",
                "data": history
            }
            
        except Exception as e:
            logger.error(f"Error getting usage history: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @abstractmethod
    async def process_request(self, request_data: Any, current_user: str) -> Dict[str, Any]:
        """Abstract method to be implemented by each AI model controller"""
        pass
