import time
from typing import Any, Dict, List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.logging import logger
from models.asset import ModalityEnum
from services.chunking import ChunkingService
from services.database import DatabaseService
from services.media_processor import MediaProcessorService
from services.upload import UploadService

class IngestionService:
    """Service orchestrating the complete ingestion pipeline from file upload to database insertion."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the ingestion service with dependencies."""
        self.db = db
        self.upload_service = UploadService(db)
        self.db_service = DatabaseService(db)

    async def ingest_file(self, upload_file: UploadFile) -> Dict[str, Any]:
        """Orchestrate file saving, preprocessing, chunking, and database insertion."""
        start_time = time.time()
        
        # 1. Store file and register asset metadata record
        asset = await self.upload_service.save_file(upload_file)
        
        logger.info(
            f"Starting media ingestion pipeline for Asset ID: {asset.id} "
            f"| filename: {asset.filename}"
        )
        
        chunks_data: List[Dict[str, Any]] = []
        
        try:
            # 2. Extract contents and build chunk representations by modality
            if asset.modality == ModalityEnum.TEXT:
                raw_text = MediaProcessorService.extract_text(asset.file_path)
                chunks_data = ChunkingService.chunk_text(raw_text)
                
            elif asset.modality == ModalityEnum.AUDIO:
                audio_duration = MediaProcessorService.get_duration(asset.file_path)
                chunks_data = ChunkingService.chunk_audio(audio_duration)
                
            elif asset.modality == ModalityEnum.VIDEO:
                video_duration, _, frames = MediaProcessorService.process_video(
                    asset.file_path, str(asset.id), settings.STORAGE_DIR
                )
                chunks_data = ChunkingService.chunk_video(video_duration, frames)
                
            # 3. Associate chunks with the parent asset and set embedding to None (NULL)
            for chunk in chunks_data:
                chunk["asset_id"] = asset.id
                chunk["embedding"] = None
                
            # 4. Save chunk records in bulk
            logger.info(
                f"Bulk inserting {len(chunks_data)} chunks to database "
                f"for Asset ID: {asset.id}"
            )
            await self.db_service.add_asset_chunks(chunks_data)
            
            elapsed_time = time.time() - start_time
            logger.info(
                f"Successfully processed Asset ID: {asset.id} in {elapsed_time:.2f}s "
                f"| Chunks created: {len(chunks_data)} | Storage: /storage/assets/{asset.id}/"
            )
            
            return {
                "asset_id": str(asset.id),
                "status": "processed",
                "chunks_created": len(chunks_data)
            }
            
        except Exception as err:
            logger.error(
                f"Ingestion pipeline failure for Asset ID {asset.id}: {str(err)}"
            )
            raise
