from fastapi import FastAPI
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router
from config.mongodb import MongoDB
import logging

# Configure logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ZenleadAI-Studio Backend")

app.include_router(auth_router)
app.include_router(user_router)

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
