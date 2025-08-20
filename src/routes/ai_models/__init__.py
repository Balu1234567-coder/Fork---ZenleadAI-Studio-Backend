from fastapi import APIRouter
from .ai_models_routes import router as ai_models_routes
from .usage_history import router as usage_routes
from .long_form_book_routes import router as long_form_book_routes
from .settings_routes import router as settings_routes  # ADD THIS
from .ai_projects_routes import router as ai_projects_routes

# Create main AI models router
ai_models_router = APIRouter(prefix="/api/ai", tags=["AI Models"])

# Include routes
ai_models_router.include_router(ai_models_routes)
ai_models_router.include_router(usage_routes)
ai_models_router.include_router(long_form_book_routes)
ai_models_router.include_router(settings_routes)  # ADD THIS
ai_models_router.include_router(ai_projects_routes)  # ADD THIS
