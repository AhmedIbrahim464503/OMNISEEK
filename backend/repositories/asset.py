import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset, ModalityEnum
from repositories.base import BaseRepository

class AssetRepository(BaseRepository[Asset]):
    """Repository implementation for database access operations on the Asset model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the repository binding it to the Asset model and DB session."""
        super().__init__(Asset, db)

    async def create_asset(
        self, filename: str, file_path: str, modality: ModalityEnum
    ) -> Asset:
        """Create and write a new Asset entity to the database session."""
        asset = Asset(
            filename=filename,
            file_path=file_path,
            modality=modality
        )
        self.db.add(asset)
        return asset

    async def get_asset_by_id(self, asset_id: uuid.UUID) -> Optional[Asset]:
        """Fetch an Asset database record uniquely matching the provided UUID."""
        stmt = select(Asset).filter(Asset.id == asset_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_assets(self, skip: int = 0, limit: int = 100) -> List[Asset]:
        """Fetch multiple Asset database records with standard pagination limit offsets."""
        stmt = select(Asset).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
