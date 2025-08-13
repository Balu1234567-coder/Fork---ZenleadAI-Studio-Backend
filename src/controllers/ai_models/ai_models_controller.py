from typing import List, Optional, Dict, Any
from src.config.mongodb import MongoDB
from src.models.ai_models.base_ai_model import AIModelCategory, AIModelStatus, UsageHistoryResponse  # ADDED UsageHistoryResponse
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class AIModelsController:
    @staticmethod
    def _prepare_document_data(doc: dict) -> dict:
        """Convert ObjectId to string"""
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_all_models(
        self,
        category: Optional[AIModelCategory] = None,
        status: Optional[AIModelStatus] = None,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all AI models with filtering and pagination"""
        try:
            models_collection = await MongoDB.get_collection("ai_models")
            
            # Build query filters
            query = {}
            if category:
                query["category"] = category.value
            if status:
                query["status"] = status.value
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}},
                    {"features": {"$in": [{"$regex": search, "$options": "i"}]}},
                    {"tags": {"$in": [{"$regex": search, "$options": "i"}]}},
                    {"extra_info.labels": {"$in": [{"$regex": search, "$options": "i"}]}}
                ]
            
            # Get total count for pagination
            total_count = await models_collection.count_documents(query)
            
            # Get models with pagination
            cursor = models_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
            
            models = []
            async for model in cursor:
                models.append(self._prepare_document_data(model))
            
            return {
                "models": models,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting AI models: {str(e)}")
            raise e

    async def get_model_by_slug(self, slug: str) -> Dict[str, Any]:
        """Get AI model by slug"""
        try:
            models_collection = await MongoDB.get_collection("ai_models")
            model = await models_collection.find_one({"slug": slug})
            
            if not model:
                raise ValueError(f"AI Model with slug '{slug}' not found")
            
            return self._prepare_document_data(model)
            
        except Exception as e:
            logger.error(f"Error getting AI model by slug: {str(e)}")
            raise e

    async def get_model_metadata(self, slug: str) -> Dict[str, Any]:
        """Get structured metadata for AI model"""
        try:
            model = await self.get_model_by_slug(slug)
            
            metadata = {
                "basic_info": {
                    "id": model.get("_id"),
                    "name": model.get("name"),
                    "slug": model.get("slug"),
                    "display_name": model.get("extra_info", {}).get("display_name", model.get("name")),
                    "category": model.get("category"),
                    "description": model.get("description"),
                    "detailed_description": model.get("extra_info", {}).get("description_detail"),
                    "status": model.get("status")
                },
                "technical_specs": {
                    "input_types": model.get("input_types", []),
                    "output_types": model.get("output_types", []),
                    "features": model.get("features", []),
                    "estimated_time": model.get("estimated_time"),
                    "success_rate": model.get("success_rate")
                },
                "pricing": {
                    "credits_per_use": model.get("pricing", {}).get("credits_per_use"),
                    "premium_credits": model.get("pricing", {}).get("premium_credits"),
                    "pricing_info": model.get("pricing", {})
                },
                "labels_and_tags": {
                    "labels": model.get("extra_info", {}).get("labels", []),
                    "tags": model.get("tags", [])
                },
                "timestamps": {
                    "created_at": model.get("created_at"),
                    "updated_at": model.get("updated_at")
                },
                "extra_info": model.get("extra_info", {})
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting AI model metadata: {str(e)}")
            raise e

    async def get_categories(self) -> Dict[str, Any]:
        """Get all categories with model counts"""
        try:
            models_collection = await MongoDB.get_collection("ai_models")
            
            # Aggregate categories with counts
            pipeline = [
                {"$match": {"status": "active"}},
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "models": {"$push": {
                        "name": "$name",
                        "slug": "$slug",
                        "description": "$description"
                    }}
                }},
                {"$sort": {"count": -1}}
            ]
            
            categories = []
            async for category in models_collection.aggregate(pipeline):
                categories.append({
                    "category": category["_id"],
                    "count": category["count"],
                    "models": category["models"]
                })
            
            return {"categories": categories}
            
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            raise e

    async def get_popular_models(self, limit: int = 10) -> Dict[str, Any]:
        """Get popular models based on tags and success rate"""
        try:
            models_collection = await MongoDB.get_collection("ai_models")
            
            # Query for popular models
            query = {
                "status": "active",
                "$or": [
                    {"tags": {"$in": ["Popular", "popular"]}},
                    {"success_rate": {"$gte": 95}}
                ]
            }
            
            cursor = models_collection.find(query).sort("success_rate", -1).limit(limit)
            
            models = []
            async for model in cursor:
                models.append(self._prepare_document_data(model))
            
            return {"popular_models": models}
            
        except Exception as e:
            logger.error(f"Error getting popular models: {str(e)}")
            raise e  # FIXED: Added missing raise e

    # ADDED: New method for usage history
    async def get_user_usage_history(
        self, 
        slug: str, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's usage history for a specific AI model"""
        try:
            # Get AI model info first
            models_collection = await MongoDB.get_collection("ai_models")
            model = await models_collection.find_one({"slug": slug})
            
            if not model:
                raise ValueError(f"AI Model with slug '{slug}' not found")
            
            # Get usage history
            usage_collection = await MongoDB.get_collection("ai_usage_history")
            
            cursor = usage_collection.find({
                "user_id": user_id,
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
            
            return {"usage_history": history}
            
        except Exception as e:
            logger.error(f"Error getting usage history: {str(e)}")
            raise e
