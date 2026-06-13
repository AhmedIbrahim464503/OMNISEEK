from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from core.logging import logger

# Initialize async engine with connection pooling and pre-ping safety
engine = create_async_engine(
    settings.DB_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db() -> None:
    """Initialize base database state and enable required extensions."""
    logger.info("Running database startup initialization...")
    async with engine.begin() as conn:
        # Enable the pgvector extension on the database instance
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    logger.info("Database initialization completed.")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injector yielding a database session context."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as err:
            logger.error(f"Database transaction error occurred: {str(err)}")
            raise
        finally:
            await session.close()
