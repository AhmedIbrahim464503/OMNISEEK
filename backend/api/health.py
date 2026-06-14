import os
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from core.db import get_db, engine
from core.config import settings
from services.cache import CacheService
from core.celery import celery_app
from services.ai_model_manager import AIModelManager

router = APIRouter(prefix="/health", tags=["Health Checks"])

@router.get("/live")
async def liveness() -> Dict[str, str]:
    """Liveness probe validating basic server process health."""
    return {"status": "alive", "service": "omniseek-backend"}

@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Readiness probe validating database connectivity."""
    try:
        # DB check
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "service": "omniseek-backend"}
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(err)}"
        )

@router.get("/deep")
async def deep_health(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Deep check probe analyzing database, redis, celery, storage path, and model statuses."""
    health_results = {
        "status": "healthy",
        "database": "ok",
        "redis": "ok",
        "celery": "ok",
        "storage": "ok",
        "models": "ok"
    }
    
    # 1. Database Check
    try:
        await db.execute(text("SELECT 1"))
    except Exception as err:
        health_results["database"] = f"unhealthy: {str(err)}"
        health_results["status"] = "unhealthy"

    # 2. Redis Check
    try:
        redis_client = CacheService.get_client()
        await redis_client.ping()
    except Exception as err:
        health_results["redis"] = f"unhealthy: {str(err)}"
        health_results["status"] = "unhealthy"

    # 3. Celery Check
    try:
        insp = celery_app.control.inspect(timeout=1.0)
        stats = insp.stats()
        if stats is None or len(stats) == 0:
            health_results["celery"] = "warning: no active workers detected"
        else:
            health_results["celery"] = "ok"
    except Exception as err:
        health_results["celery"] = f"unhealthy: {str(err)}"
        health_results["status"] = "unhealthy"

    # 4. Storage Check
    storage_path = os.getenv("STORAGE_DIR", "storage")
    try:
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)
        # Test write access
        test_file_path = os.path.join(storage_path, ".healthcheck")
        with open(test_file_path, "w") as f:
            f.write("ok")
        os.remove(test_file_path)
    except Exception as err:
        health_results["storage"] = f"unhealthy: {str(err)}"
        health_results["status"] = "unhealthy"

    # 5. Model Manager Status
    try:
        manager = AIModelManager()
        # Verify class initialization does not raise errors
        health_results["models"] = "ok"
    except Exception as err:
        health_results["models"] = f"unhealthy: {str(err)}"
        health_results["status"] = "unhealthy"

    if health_results["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_results
        )
        
    return health_results
