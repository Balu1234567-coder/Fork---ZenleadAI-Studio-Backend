from motor.motor_asyncio import AsyncIOMotorClient
from .env import env_config
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls, retries=3, delay=2):
        if cls.db is not None:
            logger.info("MongoDB already connected")
            return
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Connection attempt {attempt}/{retries} to MongoDB with URI: {env_config.MONGO_URI[:30]}...")
                cls.client = AsyncIOMotorClient(env_config.MONGO_URI, maxPoolSize=10, minPoolSize=1)
                cls.db = cls.client[env_config.DATABASE_NAME]
                await cls.db.command("ping")
                logger.info("MongoDB connected successfully")
                return
            except Exception as e:
                logger.error(f"Attempt {attempt}/{retries} failed: {str(e)}")
                cls.db = None
                cls.client = None
                if attempt == retries:
                    raise Exception(f"Failed to connect to MongoDB after {retries} attempts: {str(e)}")
                await asyncio.sleep(delay)

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            cls.db = None
            cls.client = None
            logger.info("MongoDB connection closed")

    @classmethod
    async def get_collection(cls, collection_name: str):
        if cls.db is None:
            logger.warning("Database not connected, attempting to connect")
            await cls.connect()
        if cls.db is None:
            logger.error("Failed to connect to database")
            raise Exception("Database not connected")
        return cls.db[collection_name]