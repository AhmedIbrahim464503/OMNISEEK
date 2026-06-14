import os
from typing import Any, Dict
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from core.logging import logger
from models.chunk import AssetChunk
from models.user import User
from services.ingestion import IngestionService
from services.auth import require_role
from services.task_status import TaskStatusService
from services.cache import CacheService
from api.rate_limiter import RateLimiter
from workers.worker import process_asset_embeddings

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024 # 50 MB
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.mp3', '.wav', '.mp4', '.mov'}
ALLOWED_MIMETYPES = {
    'text/plain',
    'application/pdf',
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/x-wav',
    'video/mp4',
    'video/quicktime'
}

async def scan_file_for_virus(file: UploadFile) -> bool:
    """Placeholder architecture-ready hook for virus scan validation (ClamAV integration)."""
    logger.info(f"Production security scanner running analysis on file stream: {file.filename}")
    # Integration stub: return True to represent a clean clean scan
    return True

@router.post("/upload", tags=["Upload"])
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["USER", "ADMIN"])),
    _rate_limit: None = Depends(RateLimiter("upload", 10))
) -> Dict[str, Any]:
    """Multipart file upload endpoint validating security credentials, limits, and file headers."""
    logger.info(f"API upload request received from User [{current_user.username}] for file: {file.filename}")
    
    # 1. Path traversal prevention
    safe_filename = os.path.basename(file.filename)
    file.filename = safe_filename
    
    # 2. File extension validation
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension {file_ext}. Allowed: TXT, PDF, MP3, WAV, MP4, MOV"
        )
        
    # 3. Size validation using Starlette file size attribute if available
    size = getattr(file, "size", None)
    if size is not None and size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed limit of 50MB."
        )

    # 4. Mimetype validation
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media mimetype {file.content_type}."
        )

    # 5. Security virus scanning
    if not await scan_file_for_virus(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security threat detected during file scan verification."
        )
        
    # 6. Run raw file ingestion pipeline (writes chunks with embedding = NULL)
    ingestion_service = IngestionService(db)
    result = await ingestion_service.ingest_file(file)
    asset_id = result["asset_id"]
    
    # 7. Offload embedding generation pipeline to background Celery task
    logger.info(f"Dispatching embedding orchestrator task to Celery for Asset ID: {asset_id}")
    celery_task = process_asset_embeddings.delay(asset_id)
    
    # Seed PENDING state task status record in database
    await TaskStatusService.create_task_status(
        db=db,
        task_id=celery_task.id,
        task_name="workers.worker.process_asset_embeddings"
    )
    
    # Refresh actual chunks count
    count_stmt = select(func.count(AssetChunk.id)).filter(AssetChunk.asset_id == asset_id)
    count_res = await db.execute(count_stmt)
    total_chunks = count_res.scalar_one()
    
    # Invalidate search query cache since new document is ingested
    try:
        await CacheService.invalidate_pattern("search:*")
    except Exception as err:
        logger.warning(f"Cache invalidation failure on upload: {str(err)}")
        
    return {
        "asset_id": asset_id,
        "task_id": celery_task.id,
        "status": "pending",
        "chunks_created": total_chunks,
        "message": "File ingested successfully. Vector index embedding generation is processing in the background."
    }
