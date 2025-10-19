from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine
from typing import AsyncGenerator
from app.core.config import Config
from sqlalchemy.orm import sessionmaker

# Create async engine
async_engine = create_async_engine(
    Config.DATABASE_URL,
    echo=False,  # set True for SQL logging
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Convert the async URL to a sync one automatically
SYNC_DATABASE_URL = Config.DATABASE_URL.replace("+asyncpg", "")

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)