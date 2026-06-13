from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from core.config import settings
from core.db import init_db
from core.logging import setup_logging, logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager handling application setup and teardown."""
    setup_logging()
    logger.info("Initializing OMNISEEK application lifecycle startup...")
    
    # Execute database initializations (enabling extensions)
    await init_db()
    
    yield
    
    logger.info("Tearing down OMNISEEK application lifecycle shutdown...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include primary API router
app.include_router(api_router)

@app.get("/health", tags=["Health Checks"])
async def health_check() -> Dict[str, str]:
    """Retrieve operational status of the service."""
    logger.info("Health check endpoint invoked.")
    return {
        "status": "ok",
        "service": "omniseek-backend"
    }
