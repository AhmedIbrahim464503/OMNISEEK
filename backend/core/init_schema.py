import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings
from core.logging import setup_logging, logger
from core.db import init_db
from models.base import Base
# Import all models to ensure they are registered with the Base.metadata
from models.asset import Asset
from models.chunk import AssetChunk
from models.search_log import SearchLog
from models.evaluation_run import EvaluationRun
from models.performance_log import SearchPerformanceLog
from models.user import User
from models.task_status import TaskStatus

async def run_init() -> None:
    """Establish postgres pgvector extension and create all declarative schemas."""
    setup_logging()
    logger.info("Initializing database extension and schema mapping...")
    
    # Enable vector extension on startup
    await init_db()
    
    # Connect and build schemas
    engine = create_async_engine(settings.DB_URL, echo=settings.DEBUG)
    async with engine.begin() as conn:
        logger.info("Creating application tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    await engine.dispose()
    logger.info("Database schema sync completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_init())
