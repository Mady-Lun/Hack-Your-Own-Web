from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import Config
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator

# async engine object
async_engine = create_async_engine(
    url=Config.DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
