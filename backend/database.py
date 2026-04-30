from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from config import settings

# PostgreSQL Setup
engine = create_async_engine(settings.POSTGRES_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# MongoDB Setup
mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
mongo_db = mongo_client["ims_database"]
signals_collection = mongo_db["signals"]

# Redis Setup
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
