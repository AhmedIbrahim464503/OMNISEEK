import os
import shutil
import uuid
from typing import Tuple
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import DatabaseError, ValidationError
from core.logging import logger
from models.asset import Asset, ModalityEnum
from services.database import DatabaseService

# Supported extension map mapping to respective ModalityEnums
SUPPORTED_EXTENSIONS = {
    ".txt": ModalityEnum.TEXT,
    ".pdf": ModalityEnum.TEXT,
    ".mp3": ModalityEnum.AUDIO,
    ".wav": ModalityEnum.AUDIO,
    ".mp4": ModalityEnum.VIDEO,
    ".mov": ModalityEnum.VIDEO,
}

class UploadService:
    """Service handling multi-modal file uploads, storage preparation, and metadata registration."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the upload service with an active database session."""
        self.db = db
        self.db_service = DatabaseService(db)

    def _validate_and_get_modality(self, filename: str) -> Tuple[str, ModalityEnum]:
        """Validate the file name format and return its normalized extension and modality."""
        if not filename or "." not in filename:
            raise ValidationError(f"Filename '{filename}' lacks a valid extension suffix.")
            
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"File format '{ext}' is unsupported. "
                f"Supported types: {list(SUPPORTED_EXTENSIONS.keys())}"
            )
            
        return ext, SUPPORTED_EXTENSIONS[ext]

    def _prepare_storage(self, asset_id: uuid.UUID) -> str:
        """Prepare the directory tree for localized asset storage isolation."""
        asset_dir = os.path.join(settings.STORAGE_DIR, "assets", str(asset_id))
        subdirectories = ["raw", "frames", "audio", "processed"]
        
        for subdir in subdirectories:
            target_path = os.path.join(asset_dir, subdir)
            os.makedirs(target_path, exist_ok=True)
            
        return asset_dir

    async def save_file(self, upload_file: UploadFile) -> Asset:
        """Validate, store, and register the uploaded file into the database."""
        filename = upload_file.filename or "unnamed_file"
        _, modality = self._validate_and_get_modality(filename)
        
        # Pre-assign asset ID to synchronize path naming
        asset_id = uuid.uuid4()
        asset_dir = self._prepare_storage(asset_id)
        raw_file_path = os.path.join(asset_dir, "raw", filename)
        
        logger.info(f"Storing upload '{filename}' under modality '{modality.value}'...")
        
        # Save raw upload streams
        try:
            with open(raw_file_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as err:
            logger.error(f"File system write failure for {filename}: {str(err)}")
            if os.path.exists(asset_dir):
                shutil.rmtree(asset_dir)
            raise ValidationError(f"Failed to write file stream to storage: {str(err)}")
            
        # Create database asset entry
        try:
            asset = Asset(
                id=asset_id,
                filename=filename,
                file_path=raw_file_path,
                modality=modality
            )
            self.db.add(asset)
            await self.db.commit()
            await self.db.refresh(asset)
            
            logger.info(f"Asset metadata persisted successfully: ID={asset.id}")
            return asset
        except Exception as err:
            logger.error(f"Database persist failure for asset record: {str(err)}")
            if os.path.exists(asset_dir):
                shutil.rmtree(asset_dir)
            await self.db.rollback()
            raise DatabaseError(f"Database error during upload registration: {str(err)}")
