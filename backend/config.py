import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_URL: str = os.getenv("POSTGRES_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/ims")
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "1000"))

settings = Settings()
