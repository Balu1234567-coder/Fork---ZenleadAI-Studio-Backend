from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any
from src.controllers.ai_models.ai_usage_controller import AIUsageController
from src.models.ai_models.usage_history import UsageStatus, UsageHistoryCreate
from src.middleware.auth import get_current_user

router = APIRouter()
controller = AIUsageController()

@router.post(
    "/usage",
    response_model=Dict[str, Any],
    summary="Create usage record",
    description="Create a new AI model usage record and deduct credits"
)
async def create_usage_record(
    usage_data: UsageHistoryCreate,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new usage record for AI model"""
    try:
        usage_id = await controller.create_usage_record(current_user, usage_data)
        return {
            "status": 200,
            "success": True,
            "message": "Usage record created successfully",
            "data": {"usage_id": usage_id}
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create usage record: {str(e)}")

@router.get(
    "/usage/history",
    response_model=Dict[str, Any],
    summary="Get user's usage history",
    description="Retrieve user's AI model usage history with filtering"
)
async def get_usage_history(
    current_user: str = Depends(get_current_user),
    ai_model_slug: Optional[str] = Query(None, description="Filter by AI model"),
    status: Optional[UsageStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Get user's usage history"""
    try:
        data = await controller.get_user_usage_history(
            current_user, ai_model_slug, status, limit, offset
        )
        return {
            "status": 200,
            "success": True,
            "message": "Usage history retrieved successfully",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage history: {str(e)}")

@router.get(
    "/usage/{usage_id}",
    response_model=Dict[str, Any],
    summary="Get usage detail",
    description="Get detailed information about a specific usage record"
)
async def get_usage_detail(
    usage_id: str,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed usage record"""
    try:
        detail = await controller.get_usage_detail(usage_id, current_user)
        return {
            "status": 200,
            "success": True,
            "message": "Usage detail retrieved successfully",
            "data": detail
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage detail: {str(e)}")

@router.get(
    "/usage/stats",
    response_model=Dict[str, Any],
    summary="Get usage statistics",
    description="Get user's usage statistics by AI model"
)
async def get_usage_stats(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's usage statistics"""
    try:
        stats = await controller.get_usage_stats(current_user)
        return {
            "status": 200,
            "success": True,
            "message": "Usage statistics retrieved successfully",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage statistics: {str(e)}")

@router.put(
    "/usage/{usage_id}/status",
    response_model=Dict[str, Any],
    summary="Update usage status",
    description="Update usage record status and results (internal use)"
)
async def update_usage_status(
    usage_id: str,
    status: UsageStatus,
    output_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """Update usage record status - mainly for internal processing"""
    try:
        await controller.update_usage_status(
            usage_id, status, output_data, error_message
        )
        return {
            "status": 200,
            "success": True,
            "message": "Usage status updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update usage status: {str(e)}")
