from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

logger.info(f"Initializing Async Database Engine: pool_size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}")
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=30,
    pool_pre_ping=True
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
