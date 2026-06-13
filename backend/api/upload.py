from typing import Any, Dict
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from core.logging import logger
from models.chunk import AssetChunk
from services.ingestion import IngestionService
from services.processing_orchestrator import ProcessingOrchestrator

router = APIRouter()

@router.post("/upload", tags=["Upload"])
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Multipart file upload endpoint that triggers the ingestion and embedding pipelines."""
    logger.info(f"API upload request received for file: {file.filename}")
    
    # 1. Run raw file ingestion pipeline
    ingestion_service = IngestionService(db)
    result = await ingestion_service.ingest_file(file)
    
    # 2. Run AI model embedding generator pipeline
    asset_id = result["asset_id"]
    orchestrator = ProcessingOrchestrator(db)
    logger.info(f"Triggering embedding generation pipeline for Asset ID: {asset_id}")
    await orchestrator.process_asset_embeddings(asset_id)
    
    # Refresh actual chunks count (Whisper segmentation can update total chunk records)
    count_stmt = select(func.count(AssetChunk.id)).filter(AssetChunk.asset_id == asset_id)
    count_res = await db.execute(count_stmt)
    total_chunks = count_res.scalar_one()
    
    return {
        "asset_id": asset_id,
        "status": "processed",
        "chunks_created": total_chunks
    }

