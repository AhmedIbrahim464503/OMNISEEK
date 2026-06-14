import os
import uuid
from typing import Any, Dict, List
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import DatabaseError
from core.logging import logger
from models.asset import Asset, ModalityEnum
from models.chunk import AssetChunk
from services.audio_embedding import AudioEmbeddingService
from services.embedding import EmbeddingService

class ProcessingOrchestrator:
    """Connects Phase 3 raw ingestion output to Phase 4 AI model embeddings and database updates."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the orchestrator with an active database session."""
        self.db = db

    async def process_asset_embeddings(self, asset_id: uuid.UUID) -> int:
        """Process all raw chunks of the asset, generate vector embeddings, and update DB."""
        # 1. Fetch parent asset record
        stmt = select(Asset).filter(Asset.id == asset_id)
        result = await self.db.execute(stmt)
        asset = result.scalars().first()
        if not asset:
            logger.error(f"Asset ID {asset_id} not found in database.")
            return 0
            
        logger.info(
            f"Orchestrator starting embedding processing for asset: '{asset.filename}' "
            f"({asset.modality.value})"
        )
        
        # 2. Get existing chunks where embedding is NULL
        chunks_stmt = (
            select(AssetChunk)
            .filter(AssetChunk.asset_id == asset_id, AssetChunk.embedding == None)
        )
        chunks_result = await self.db.execute(chunks_stmt)
        raw_chunks = chunks_result.scalars().all()
        
        if not raw_chunks and asset.modality not in (ModalityEnum.VIDEO, ModalityEnum.AUDIO):
            logger.info(f"No raw chunks to process for Asset ID: {asset_id}")
            return 0
            
        chunks_updated = 0
        
        try:
            if asset.modality == ModalityEnum.TEXT:
                # Process text chunks in bulk
                batch = []
                for chunk in raw_chunks:
                    try:
                        vector = EmbeddingService.embed_text(chunk.content)
                        batch.append({"id": chunk.id, "embedding": vector})
                    except Exception as err:
                        logger.error(f"Skipped text chunk {chunk.id} due to embedding error: {str(err)}")
                        continue
                if batch:
                    await self._bulk_update_embeddings(batch)
                    chunks_updated += len(batch)
                    
            elif asset.modality == ModalityEnum.AUDIO:
                # Audio: run Whisper on raw file, delete placeholders, and insert transcribed text chunks
                logger.info("Transcribing and embedding audio using Whisper + BGE-M3...")
                real_chunks = AudioEmbeddingService.process_audio(asset.file_path)
                
                # Remove Phase 3 placeholder chunks
                del_stmt = delete(AssetChunk).filter(AssetChunk.asset_id == asset_id)
                await self.db.execute(del_stmt)
                
                # Bulk insert real transcribed chunks
                from services.database import DatabaseService
                db_service = DatabaseService(self.db)
                for chunk in real_chunks:
                    chunk["asset_id"] = asset_id
                    
                await db_service.add_asset_chunks(real_chunks)
                chunks_updated += len(real_chunks)
                
            elif asset.modality == ModalityEnum.VIDEO:
                # Video:
                # 1. Update visual frame chunks (Phase 3) using CLIP embeddings
                visual_batch = []
                for chunk in raw_chunks:
                    frames_metadata = chunk.chunk_metadata.get("frames", [])
                    if not frames_metadata:
                        continue
                    # Embed the first frame in the interval as visual representative
                    first_frame_path = frames_metadata[0]["frame_path"]
                    try:
                        vector = EmbeddingService.embed_image(first_frame_path)
                        visual_batch.append({"id": chunk.id, "embedding": vector})
                    except Exception as err:
                        logger.error(f"Skipped visual frame chunk {chunk.id} due to CLIP error: {str(err)}")
                        continue
                if visual_batch:
                    await self._bulk_update_embeddings(visual_batch)
                    chunks_updated += len(visual_batch)
                    
                # 2. Transcribe demuxed audio track and insert as additional text chunks
                filename = os.path.basename(asset.file_path)
                base_name, _ = os.path.splitext(filename)
                audio_path = os.path.join(
                    settings.STORAGE_DIR,
                    "assets",
                    str(asset_id),
                    "audio",
                    f"{base_name}_audio.mp3"
                )
                
                # Check if audio path exists and is not a mock placeholder (which is a 36-byte text file)
                is_valid_audio = False
                if os.path.exists(audio_path):
                    if os.path.getsize(audio_path) > 1000:
                        is_valid_audio = True
                    else:
                        try:
                            with open(audio_path, "r", errors="ignore") as f:
                                content = f.read(100)
                                if "MOCK_DEMUXED_AUDIO_TRACK_PLACEHOLDER" not in content:
                                    is_valid_audio = True
                        except Exception:
                            pass

                if is_valid_audio:
                    logger.info("Transcribing demuxed video audio track using Whisper...")
                    audio_chunks = AudioEmbeddingService.process_audio(audio_path)
                    
                    # Offset indexes to avoid collisions with visual indexes
                    visual_count = len(raw_chunks)
                    from services.database import DatabaseService
                    db_service = DatabaseService(self.db)
                    for idx, chunk in enumerate(audio_chunks):
                        chunk["asset_id"] = asset_id
                        chunk["chunk_index"] = visual_count + idx
                        
                    await db_service.add_asset_chunks(audio_chunks)
                    chunks_updated += len(audio_chunks)
                else:
                    logger.warning(f"Audio track for video {asset_id} is missing or is a mock placeholder. Skipping Whisper transcription.")
                    
            await self.db.commit()
            logger.info(
                f"Orchestration completed successfully. Persisted {chunks_updated} "
                f"embeddings for Asset ID: {asset_id}"
            )
            return chunks_updated
            
        except Exception as err:
            await self.db.rollback()
            logger.error(f"Transaction failed, rolling back orchestrator changes: {str(err)}")
            raise DatabaseError(f"Embedding pipeline execution failed: {str(err)}")

    async def _bulk_update_embeddings(self, batch: List[Dict[str, Any]], batch_size: int = 50) -> None:
        """Batch update chunk embedding fields in database."""
        for i in range(0, len(batch), batch_size):
            chunk_batch = batch[i:i + batch_size]
            for record in chunk_batch:
                stmt = (
                    update(AssetChunk)
                    .filter(AssetChunk.id == record["id"])
                    .values(embedding=record["embedding"])
                )
                await self.db.execute(stmt)
