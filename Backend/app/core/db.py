from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.config import Config
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

# async engine object
async_engine = AsyncEngine(
    create_engine(
        url=Config.DATABASE_URL,
    )
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
