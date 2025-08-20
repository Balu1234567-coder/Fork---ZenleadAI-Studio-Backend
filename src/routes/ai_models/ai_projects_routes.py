from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict, Any, List
from src.controllers.ai_models.ai_usage_controller import AIUsageController
from src.middleware.auth import get_current_user
from datetime import datetime

router = APIRouter()
controller = AIUsageController()

@router.get(
    "/ai/projects",
    response_model=Dict[str, Any],
    summary="Get All User Projects",
    description="Get all AI projects across different model types for sidebar"
)
async def get_all_user_projects(
    current_user: str = Depends(get_current_user),
    project_type: Optional[str] = Query(None, description="Filter by AI model type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Get all user projects for sidebar management"""
    try:
        # Get usage history with optimized projection
        history_data = await controller.get_user_usage_history(
            user_id=current_user,
            ai_model_slug=project_type,
            limit=limit,
            offset=offset
        )
        
        projects = []
        for usage in history_data["usage_history"]:
            project = _format_project_for_sidebar(usage)
            projects.append(project)
        
        # Group projects by type for organized display
        projects_by_type = _group_projects_by_type(projects)
        
        return {
            "status": 200,
            "success": True,
            "data": {
                "projects": projects,
                "projects_by_type": projects_by_type,
                "pagination": history_data["pagination"],
                "summary": _get_projects_summary(projects)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")

def _format_project_for_sidebar(usage) -> Dict[str, Any]:
    """Format project data specifically for sidebar display"""
    
    # Base project data
    project = {
        "usage_id": usage.uid,
        "project_type": usage.ai_model_slug,
        "project_name": usage.ai_model_name,
        "status": usage.status.value,
        "created_at": usage.created_at,
        "completed_at": usage.completed_at,
        "credits_used": usage.credits_used,
        "has_results": usage.has_output,
        
        # Navigation URLs
        "project_url": f"/ai/{usage.ai_model_slug}/project/{usage.uid}",
        
        # Status indicators for UI
        "status_info": {
            "color": _get_status_color(usage.status.value),
            "icon": _get_status_icon(usage.status.value),
            "can_open": usage.status.value in ["completed", "processing", "failed"],
            "is_processing": usage.status.value == "processing",
            "progress_available": usage.status.value == "processing"
        }
    }
    
    # Add model-specific metadata
    if usage.ai_model_slug == "long-form-book":
        project.update(_extract_book_metadata(usage))
    elif usage.ai_model_slug == "image-generator":
        project.update(_extract_image_metadata(usage))
    # Add more AI models here
    
    return project

def _extract_book_metadata(usage) -> Dict[str, Any]:
    """Extract book-specific data for sidebar"""
    settings = usage.model_settings or {}
    metadata = {
        "title": settings.get("book_title", "Untitled Book"),
        "genre": settings.get("genre", ""),
        "thumbnail": "📚",  # Book emoji as default
        "subtitle": f"{settings.get('genre', 'Book')} • {settings.get('chapters_count', 0)} chapters"
    }
    
    # Add completed book stats
    if hasattr(usage, 'metadata') and usage.metadata:
        book_meta = usage.metadata.get("book_metadata", {})
        if book_meta:
            word_count = book_meta.get("total_words", 0)
            metadata["subtitle"] = f"{word_count:,} words • {settings.get('genre', 'Book')}"
    
    return metadata

def _extract_image_metadata(usage) -> Dict[str, Any]:
    """Extract image generation metadata for sidebar"""
    settings = usage.model_settings or {}
    return {
        "title": settings.get("prompt", "Image Generation")[:30] + "...",
        "genre": settings.get("style", ""),
        "thumbnail": "🎨",
        "subtitle": f"{settings.get('style', 'Image')} • {settings.get('size', 'Unknown')}"
    }

def _group_projects_by_type(projects: List[Dict]) -> Dict[str, List[Dict]]:
    """Group projects by AI model type for organized sidebar"""
    grouped = {}
    for project in projects:
        project_type = project["project_type"]
        if project_type not in grouped:
            grouped[project_type] = []
        grouped[project_type].append(project)
    
    return grouped

def _get_projects_summary(projects: List[Dict]) -> Dict[str, Any]:
    """Get project statistics for sidebar header"""
    total = len(projects)
    processing = len([p for p in projects if p["status"] == "processing"])
    completed = len([p for p in projects if p["status"] == "completed"])
    failed = len([p for p in projects if p["status"] == "failed"])
    
    return {
        "total": total,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "by_type": {
            project_type: len([p for p in projects if p["project_type"] == project_type])
            for project_type in set(p["project_type"] for p in projects)
        }
    }

def _get_status_color(status: str) -> str:
    """Get color for status indicator"""
    colors = {
        "pending": "#FFA500",     # Orange
        "processing": "#007BFF",  # Blue
        "completed": "#28A745",   # Green
        "failed": "#DC3545",      # Red
        "cancelled": "#6C757D"    # Gray
    }
    return colors.get(status, "#6C757D")

def _get_status_icon(status: str) -> str:
    """Get icon for status indicator"""
    icons = {
        "pending": "⏳",
        "processing": "⚙️",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "⏹️"
    }
    return icons.get(status, "❓")

@router.get(
    "/ai/projects/processing",
    response_model=Dict[str, Any],
    summary="Get Processing Projects",
    description="Get only processing projects for live updates"
)
async def get_processing_projects(
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get only processing projects for real-time sidebar updates"""
    try:
        from src.models.ai_models.usage_history import UsageStatus
        
        history_data = await controller.get_user_usage_history(
            user_id=current_user,
            status=UsageStatus.PROCESSING,
            limit=20
        )
        
        processing_projects = []
        for usage in history_data["usage_history"]:
            project = _format_project_for_sidebar(usage)
            processing_projects.append(project)
        
        return {
            "status": 200,
            "success": True,
            "data": {
                "processing_projects": processing_projects,
                "count": len(processing_projects)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processing projects: {str(e)}")
