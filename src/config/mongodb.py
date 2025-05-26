from motor.motor_asyncio import AsyncIOMotorClient
from .env import env_config

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect(cls):
        cls.client = AsyncIOMotorClient(env_config.MONGO_URI)
        cls.db = cls.client[env_config.DATABASE_NAME]

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()

    @classmethod
    def get_collection(cls, collection_name: str):
        if cls.db is None:
            raise Exception("Database not connected")
        return cls.db[collection_name]