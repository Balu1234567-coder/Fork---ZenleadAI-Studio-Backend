from fastapi import APIRouter
from .ai_models_routes import router as ai_models_routes

# Create main AI models router
ai_models_router = APIRouter(prefix="/api/ai", tags=["AI Models"])

# Include AI models routes
ai_models_router.include_router(ai_models_routes)

# Future individual AI model routes can be added here
# from .audio_translation_routes import router as audio_translation_router
# from .voice_cloning_routes import router as voice_cloning_router
# from .text_to_speech_routes import router as text_to_speech_router
# from .audio_enhancement_routes import router as audio_enhancement_router
# from .excel_to_charts_routes import router as excel_to_charts_router
# from .summarization_routes import router as summarization_router
# from .ats_score_routes import router as ats_score_router
# from .resume_analyzer_routes import router as resume_analyzer_router
# from .content_generation_routes import router as content_generation_router
# from .ai_video_creator_routes import router as ai_video_creator_router

# ai_models_router.include_router(audio_translation_router)
# ai_models_router.include_router(voice_cloning_router)
# ai_models_router.include_router(text_to_speech_router)
# ai_models_router.include_router(audio_enhancement_router)
# ai_models_router.include_router(excel_to_charts_router)
# ai_models_router.include_router(summarization_router)
# ai_models_router.include_router(ats_score_router)
# ai_models_router.include_router(resume_analyzer_router)
# ai_models_router.include_router(content_generation_router)
# ai_models_router.include_router(ai_video_creator_router)
