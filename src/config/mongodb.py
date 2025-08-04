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
                cls.client = AsyncIOMotorClient(
                    env_config.MONGO_URI,
                    maxPoolSize=10,
                    minPoolSize=1,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=5000,          # 5 second connection timeout
                    socketTimeoutMS=5000            # 5 second socket timeout
                )
                cls.db = cls.client[env_config.DATABASE_NAME]
                # Test connection with timeout
                await asyncio.wait_for(cls.db.command("ping"), timeout=5.0)
                logger.info("MongoDB connected successfully")
                return
            except asyncio.TimeoutError:
                logger.error(f"Attempt {attempt}/{retries} timed out after 5 seconds")
                cls.db = None
                cls.client = None
                if attempt == retries:
                    logger.warning("MongoDB connection failed - app will continue without database")
                    return  # Don't raise exception, just continue
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Attempt {attempt}/{retries} failed: {str(e)}")
                cls.db = None
                cls.client = None
                if attempt == retries:
                    logger.warning("MongoDB connection failed - app will continue without database")
                    return  # Don't raise exception, just continue
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
