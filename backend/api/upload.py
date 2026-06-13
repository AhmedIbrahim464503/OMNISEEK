from typing import Any, Dict
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from core.logging import logger
from services.ingestion import IngestionService

router = APIRouter()

@router.post("/upload", tags=["Upload"])
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Multipart file upload endpoint that triggers the ingestion preprocessing pipeline."""
    logger.info(f"API upload request received for file: {file.filename}")
    ingestion_service = IngestionService(db)
    result = await ingestion_service.ingest_file(file)
    return result
