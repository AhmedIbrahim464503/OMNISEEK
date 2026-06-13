from fastapi import APIRouter
from api.upload import router as upload_router
from api.search import router as search_router

# Primary API router registry for registration of domain endpoints
api_router = APIRouter()
api_router.include_router(upload_router, prefix="/api/v1")
api_router.include_router(upload_router, prefix="/api")
api_router.include_router(search_router, prefix="/api/v1")
api_router.include_router(search_router, prefix="/api")
