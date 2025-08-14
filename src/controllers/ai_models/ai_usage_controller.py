from typing import List, Optional, Dict, Any
from src.config.mongodb import MongoDB
from src.models.ai_models.usage_history import (
    AIUsageHistory, UsageHistoryCreate, UsageHistoryResponse, 
    UsageHistoryDetail, UsageStatus
)
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AIUsageController:
    @staticmethod
    def _prepare_document_data(doc: dict) -> dict:
        """Convert ObjectId to string"""
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc

    async def create_usage_record(
        self,
        user_id: str,
        usage_data: UsageHistoryCreate
    ) -> str:
        """Create a new usage history record and deduct credits"""
        try:
            # Get AI model info
            models_collection = await MongoDB.get_collection("ai_models")
            model = await models_collection.find_one({"slug": usage_data.ai_model_slug})
            
            if not model:
                raise ValueError(f"AI Model with slug '{usage_data.ai_model_slug}' not found")
            
            # Calculate credits required
            credits_required = model.get("pricing", {}).get("credits_per_use", 1)
            
            # Check user credits
            users_collection = await MongoDB.get_collection("users")
            user_query = {"_id": ObjectId(user_id)} if len(user_id) == 24 else {"_id": user_id}
            user = await users_collection.find_one(user_query)
            
            if not user:
                raise ValueError("User not found")
            
            if user["credits"] < credits_required:
                raise ValueError("Insufficient credits")
            
            # Create usage record
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            usage_record = AIUsageHistory(
                user_id=user_id,
                ai_model_id=str(model["_id"]),
                ai_model_slug=usage_data.ai_model_slug,
                ai_model_name=model["name"],
                model_settings=usage_data.model_settings,
                input_data=usage_data.input_data,
                metadata=usage_data.metadata,
                credits_used=credits_required,
                status=UsageStatus.PENDING
            )
            
            result = await usage_collection.insert_one(usage_record.dict(by_alias=True, exclude={"uid"}))
            
            # Deduct credits
            await users_collection.update_one(
                user_query,
                {
                    "$inc": {"credits": -credits_required},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Update usage record to mark credits as deducted
            await usage_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"credits_deducted": True, "started_at": datetime.utcnow()}}
            )
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error creating usage record: {str(e)}")
            raise e

    async def update_usage_status(
        self,
        usage_id: str,
        status: UsageStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update usage record with results"""
        try:
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
            
            if output_data:
                update_data["output_data"] = output_data
            
            if status == UsageStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow()
            
            if error_message:
                update_data["error_message"] = error_message
            
            if error_details:
                update_data["error_details"] = error_details
            
            if metadata:
                update_data["$set"] = {**update_data}
                update_data["$addToSet"] = {"metadata": {"$each": list(metadata.items())}}
            
            await usage_collection.update_one(
                {"_id": ObjectId(usage_id)},
                {"$set": update_data}
            )
            
        except Exception as e:
            logger.error(f"Error updating usage record: {str(e)}")
            raise e

    async def get_user_usage_history(
        self,
        user_id: str,
        ai_model_slug: Optional[str] = None,
        status: Optional[UsageStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's usage history with optimized queries"""
        try:
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            
            # Build query
            query = {"user_id": user_id}
            if ai_model_slug:
                query["ai_model_slug"] = ai_model_slug
            if status:
                query["status"] = status.value
            
            # Get total count
            total_count = await usage_collection.count_documents(query)
            
            # Optimized projection - only get necessary fields for listing
            projection = {
                "_id": 1,
                "ai_model_name": 1,
                "ai_model_slug": 1,
                "model_settings": 1,
                "status": 1,
                "credits_used": 1,
                "created_at": 1,
                "completed_at": 1,
                "output_data": 1,  # Just to check if has_output
                "metadata": 1
            }
            
            cursor = usage_collection.find(query, projection).sort("created_at", -1).skip(offset).limit(limit)
            
            history = []
            async for usage in cursor:
                usage = self._prepare_document_data(usage)
                
                history.append(UsageHistoryResponse(
                    _id=usage["_id"],
                    ai_model_name=usage["ai_model_name"],
                    ai_model_slug=usage["ai_model_slug"],
                    model_settings=usage.get("model_settings", {}),
                    status=usage["status"],
                    credits_used=usage["credits_used"],
                    created_at=usage["created_at"],
                    completed_at=usage.get("completed_at"),
                    has_output=bool(usage.get("output_data", {})),
                    metadata=usage.get("metadata", {})
                ))
            
            return {
                "usage_history": history,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting usage history: {str(e)}")
            raise e

    async def get_usage_detail(self, usage_id: str, user_id: str) -> UsageHistoryDetail:
        """Get detailed usage record"""
        try:
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            
            usage = await usage_collection.find_one({
                "_id": ObjectId(usage_id),
                "user_id": user_id  # Security: ensure user owns this record
            })
            
            if not usage:
                raise ValueError("Usage record not found")
            
            usage = self._prepare_document_data(usage)
            
            return UsageHistoryDetail(
                _id=usage["_id"],
                ai_model_name=usage["ai_model_name"],
                ai_model_slug=usage["ai_model_slug"],
                model_settings=usage.get("model_settings", {}),
                status=usage["status"],
                credits_used=usage["credits_used"],
                input_data=usage.get("input_data", {}),
                output_data=usage.get("output_data", {}),
                metadata=usage.get("metadata", {}),
                error_message=usage.get("error_message"),
                created_at=usage["created_at"],
                started_at=usage.get("started_at"),
                completed_at=usage.get("completed_at")
            )
            
        except Exception as e:
            logger.error(f"Error getting usage detail: {str(e)}")
            raise e

    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's usage statistics"""
        try:
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": {
                        "model_slug": "$ai_model_slug",
                        "status": "$status"
                    },
                    "count": {"$sum": 1},
                    "total_credits": {"$sum": "$credits_used"}
                }},
                {"$group": {
                    "_id": "$_id.model_slug",
                    "stats": {
                        "$push": {
                            "status": "$_id.status",
                            "count": "$count",
                            "credits": "$total_credits"
                        }
                    },
                    "total_usage": {"$sum": "$count"},
                    "total_credits": {"$sum": "$total_credits"}
                }}
            ]
            
            stats = {}
            async for stat in usage_collection.aggregate(pipeline):
                stats[stat["_id"]] = {
                    "total_usage": stat["total_usage"],
                    "total_credits": stat["total_credits"],
                    "by_status": {s["status"]: {"count": s["count"], "credits": s["credits"]} for s in stat["stats"]}
                }
            
            return {"usage_stats": stats}
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            raise e
