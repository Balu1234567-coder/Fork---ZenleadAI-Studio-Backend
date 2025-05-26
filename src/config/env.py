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