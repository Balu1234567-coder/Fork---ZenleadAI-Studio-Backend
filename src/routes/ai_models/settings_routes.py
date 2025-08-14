from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from src.controllers.ai_models.settings_controller import AIModelSettingsController
from src.middleware.auth import get_current_user

router = APIRouter()
controller = AIModelSettingsController()

@router.get(
    "/models/{model_slug}/settings",
    response_model=Dict[str, Any],
    summary="Get AI Model Settings",
    description="Get dynamic settings configuration for a specific AI model"
)
async def get_model_settings(model_slug: str) -> Dict[str, Any]:
    """
    Get dynamic settings for a specific AI model.
    Frontend can use this to build the form dynamically.
    """
    try:
        settings = await controller.get_model_settings(model_slug)
        return {
            "status": 200,
            "success": True,
            "message": "Model settings retrieved successfully",
            "data": settings
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve settings: {str(e)}")

@router.get(
    "/models/settings/all",
    response_model=Dict[str, Any],
    summary="Get All AI Model Settings",
    description="Get settings for all active AI models"
)
async def get_all_model_settings() -> Dict[str, Any]:
    """
    Get settings for all active AI models.
    Useful for frontend to know all available models and their configurations.
    """
    try:
        settings = await controller.get_all_model_settings()
        return {
            "status": 200,
            "success": True,
            "message": "All model settings retrieved successfully",
            "data": settings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve settings: {str(e)}")

@router.post(
    "/models/{model_slug}/validate",
    response_model=Dict[str, Any],
    summary="Validate User Input",
    description="Validate user input against model settings schema"
)
async def validate_user_input(
    model_slug: str,
    user_input: Dict[str, Any],
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate user input against the model's settings schema.
    Returns validation errors and cleaned data.
    """
    try:
        validation_result = await controller.validate_user_input(model_slug, user_input)
        
        return {
            "status": 200 if validation_result["valid"] else 400,
            "success": validation_result["valid"],
            "message": "Validation completed" if validation_result["valid"] else "Validation failed",
            "data": validation_result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate input: {str(e)}")

# Admin routes for updating settings
@router.put(
    "/admin/models/{model_slug}/settings",
    response_model=Dict[str, Any],
    summary="Update AI Model Settings (Admin)",
    description="Update settings configuration for a specific AI model"
)
async def update_model_settings(
    model_slug: str,
    settings_data: Dict[str, Any],
    current_user: str = Depends(get_current_user)  # Add admin check here
) -> Dict[str, Any]:
    """
    Update settings for a specific AI model.
    This is an admin-only operation.
    """
    try:
        # TODO: Add admin role check
        # if not is_admin(current_user):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        updated_settings = await controller.update_model_settings(model_slug, settings_data)
        return {
            "status": 200,
            "success": True,
            "message": "Model settings updated successfully",
            "data": updated_settings
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
