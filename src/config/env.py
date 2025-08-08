from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class EnvConfig:
    def __init__(self):
        self.MONGO_URI = os.getenv("MONGO_URI")
        self.DATABASE_NAME = os.getenv("DATABASE_NAME", "zenleadai")
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.SESSION_SECRET_KEY=os.getenv("SESSION_SECRET_KEY")
        self.GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET")
        self.GOOGLE_REDIRECT_URI=os.getenv("GOOGLE_REDIRECT_URI")
        self.FRONTEND_URI=os.getenv("FRONTEND_URI")
        self.GOOGLE_AI_STUDIO_API_KEY=os.getenv("GOOGLE_AI_STUDIO_API_KEY")
        self.RAZORPAY_KEY_ID=os.getenv("RAZORPAY_KEY_ID")
        self.RAZORPAY_KEY_SECRET=os.getenv("RAZORPAY_KEY_SECRET")

        # Validate critical variables
        if not self.MONGO_URI:
            logger.error("MONGO_URI is not set")
            raise ValueError("MONGO_URI environment variable is required")
        if not self.JWT_SECRET_KEY:
            logger.error("JWT_SECRET_KEY is not set")
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        
        logger.info("Environment variables loaded successfully")
        logger.info(f"MONGO_URI (partial): {self.MONGO_URI[:30]}...")
        logger.info(f"DATABASE_NAME: {self.DATABASE_NAME}")

env_config = EnvConfig()