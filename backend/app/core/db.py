from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import NullPool
from app.core.config import Config
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator

# async engine object with NullPool to avoid event loop conflicts in Celery workers
# NullPool creates a new connection for each request and closes it immediately after use
async_engine = create_async_engine(
    url=Config.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,  # No connection pooling - prevents event loop attachment issues
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
