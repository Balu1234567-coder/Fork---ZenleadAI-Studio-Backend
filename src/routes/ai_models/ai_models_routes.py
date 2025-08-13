from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
from src.controllers.ai_models.ai_models_controller import AIModelsController
from src.models.ai_models.base_ai_model import AIModelCategory, AIModelStatus
from src.middleware.auth import get_current_user

# Create router for AI models
router = APIRouter()

# Initialize controller
controller = AIModelsController()

@router.get(
    "/models",
    response_model=Dict[str, Any],
    summary="Get all AI models",
    description="Retrieve all available AI models with filtering and pagination"
)
async def get_all_ai_models(
    category: Optional[AIModelCategory] = Query(None, description="Filter by model category"),
    status: Optional[AIModelStatus] = Query(AIModelStatus.ACTIVE, description="Filter by model status"),
    limit: int = Query(50, ge=1, le=100, description="Number of models to return"),
    offset: int = Query(0, ge=0, description="Number of models to skip"),
    search: Optional[str] = Query(None, description="Search in model name, description, features, or tags")
) -> Dict[str, Any]:
    """
    Get all AI models with optional filtering and pagination.
    
    - **category**: Filter by model category (audio, text, image, video, data, content)
    - **status**: Filter by model status (active, inactive, maintenance, deprecated)
    - **search**: Search in model name, description, features, or tags
    - **limit**: Maximum number of results to return (1-100)
    - **offset**: Number of results to skip for pagination
    """
    try:
        data = await controller.get_all_models(category, status, limit, offset, search)
        return {
            "status": 200,
            "success": True,
            "message": f"Retrieved {len(data['models'])} AI models successfully",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI models: {str(e)}")

@router.get(
    "/models/{slug}",
    response_model=Dict[str, Any],
    summary="Get AI model by slug",
    description="Retrieve detailed information about a specific AI model"
)
async def get_ai_model_by_slug(slug: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific AI model.
    
    - **slug**: The unique slug identifier of the AI model
    """
    try:
        model = await controller.get_model_by_slug(slug)
        return {
            "status": 200,
            "success": True,
            "message": "AI Model retrieved successfully",
            "data": model
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI model: {str(e)}")

@router.get(
    "/models/{slug}/metadata",
    response_model=Dict[str, Any],
    summary="Get AI model metadata",
    description="Retrieve comprehensive structured metadata for a specific AI model"
)
async def get_ai_model_metadata(slug: str) -> Dict[str, Any]:
    """
    Get comprehensive metadata for a specific AI model including:
    - Basic information (name, description, category)
    - Technical specifications (input/output types, features)
    - Pricing and usage information
    - Performance metrics
    - Additional metadata and tags
    """
    try:
        metadata = await controller.get_model_metadata(slug)
        return {
            "status": 200,
            "success": True,
            "message": "AI Model metadata retrieved successfully",
            "data": metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AI model metadata: {str(e)}")

@router.get(
    "/categories",
    response_model=Dict[str, Any],
    summary="Get AI model categories",
    description="Retrieve all available AI model categories with model counts"
)
async def get_ai_model_categories() -> Dict[str, Any]:
    """
    Get all available AI model categories with model counts and sample models.
    """
    try:
        data = await controller.get_categories()
        return {
            "status": 200,
            "success": True,
            "message": "AI Model categories retrieved successfully",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve categories: {str(e)}")

@router.get(
    "/popular",
    response_model=Dict[str, Any],
    summary="Get popular AI models",
    description="Retrieve popular AI models based on success rate and popularity tags"
)
async def get_popular_ai_models(
    limit: int = Query(10, ge=1, le=50, description="Number of popular models to return")
) -> Dict[str, Any]:
    """
    Get popular AI models based on success rate and popularity indicators.
    
    - **limit**: Maximum number of popular models to return (1-50)
    """
    try:
        data = await controller.get_popular_models(limit)
        return {
            "status": 200,
            "success": True,
            "message": f"Retrieved {len(data['popular_models'])} popular AI models successfully",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve popular models: {str(e)}")

@router.get(
    "/models/{slug}/pricing",
    response_model=Dict[str, Any],
    summary="Get AI model pricing",
    description="Retrieve pricing information for a specific AI model"
)
async def get_ai_model_pricing(slug: str) -> Dict[str, Any]:
    """
    Get pricing information for a specific AI model.
    
    - **slug**: The unique slug identifier of the AI model
    """
    try:
        model = await controller.get_model_by_slug(slug)
        pricing_data = {
            "model_name": model.get("name"),
            "slug": model.get("slug"),
            "pricing": model.get("pricing", {}),
            "estimated_time": model.get("estimated_time"),
            "success_rate": model.get("success_rate")
        }
        
        return {
            "status": 200,
            "success": True,
            "message": "AI Model pricing retrieved successfully",
            "data": pricing_data
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pricing: {str(e)}")

@router.get(
    "/models/{slug}/usage-history",
    response_model=Dict[str, Any],
    summary="Get user's usage history for AI model",
    description="Retrieve user's usage history for a specific AI model"
)
async def get_model_usage_history(
    slug: str,
    current_user: str = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get user's usage history for a specific AI model.
    
    Requires authentication.
    """
    try:
        # CHANGED: Use the controller method instead of BaseAIController
        data = await controller.get_user_usage_history(slug, current_user, limit, offset)
        
        return {
            "status": 200,
            "success": True,
            "message": "Usage history retrieved successfully",
            "data": data["usage_history"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage history: {str(e)}")
