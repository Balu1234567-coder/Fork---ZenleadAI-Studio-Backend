from dotenv import load_dotenv
import os

load_dotenv()

class EnvConfig:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "default_db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

env_config = EnvConfig()