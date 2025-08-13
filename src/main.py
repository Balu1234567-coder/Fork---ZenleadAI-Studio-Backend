from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.auth_routes import router as auth_router
from src.routes.user_routes import router as user_router
from src.routes.conversation_routes import router as conversation_router
from src.routes.payment_routes import router as payment_router
from src.routes.ai_models import ai_models_router
from src.config.mongodb import MongoDB
import logging


# Configure logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ZenleadAI-Studio Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(conversation_router)
app.include_router(payment_router)
app.include_router(ai_models_router)  # Add this line


@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Attempting to connect to MongoDB...")
        await MongoDB.connect()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB on startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await MongoDB.close()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Failed to close MongoDB connection: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Welcome to ZenleadAI-Studio Backend"}
