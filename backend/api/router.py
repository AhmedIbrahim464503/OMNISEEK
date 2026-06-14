from fastapi import APIRouter
from api.upload import router as upload_router
from api.search import router as search_router
from api.auth import router as auth_router
from api.health import router as health_router
from api.metrics import router as metrics_router

# Primary API router registry for registration of domain endpoints
api_router = APIRouter()

# Register Authentication endpoints
api_router.include_router(auth_router)

# Register Health and Metrics endpoints
api_router.include_router(health_router)
api_router.include_router(metrics_router)

# Ingestion and Search endpoints
api_router.include_router(upload_router, prefix="/api/v1")
api_router.include_router(upload_router, prefix="/api")
api_router.include_router(search_router, prefix="/api/v1")
api_router.include_router(search_router, prefix="/api")
