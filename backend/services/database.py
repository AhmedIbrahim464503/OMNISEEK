import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset, ModalityEnum
from models.chunk import AssetChunk
from repositories.asset import AssetRepository
from repositories.chunk import ChunkRepository
from core.exceptions import DatabaseError

class DatabaseService:
    """Service wrapper managing transactions and database repository executions."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the service binding it to an active DB session and repo instances."""
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.chunk_repo = ChunkRepository(db)

    async def create_asset(
        self, filename: str, file_path: str, modality: ModalityEnum
    ) -> Asset:
        """Persist a new media asset context within a committed transactional block."""
        try:
            asset = await self.asset_repo.create_asset(filename, file_path, modality)
            await self.db.commit()
            await self.db.refresh(asset)
            return asset
        except Exception as err:
            await self.db.rollback()
            raise DatabaseError(f"Failed to create asset: {str(err)}") from err

    async def get_asset_by_id(self, asset_id: uuid.UUID) -> Optional[Asset]:
        """Fetch a single Asset record uniquely matching the provided UUID."""
        try:
            return await self.asset_repo.get_asset_by_id(asset_id)
        except Exception as err:
            raise DatabaseError(f"Failed to retrieve asset: {str(err)}") from err

    async def list_assets(self, skip: int = 0, limit: int = 100) -> List[Asset]:
        """Fetch multiple Asset records with standard pagination limit offsets."""
        try:
            return await self.asset_repo.list_assets(skip=skip, limit=limit)
        except Exception as err:
            raise DatabaseError(f"Failed to list assets: {str(err)}") from err

    async def add_asset_chunks(
        self, chunks_data: List[Dict[str, Any]]
    ) -> List[AssetChunk]:
        """Bulk insert and commit chunks for a given asset within a transaction."""
        try:
            chunks = await self.chunk_repo.insert_chunks_bulk(chunks_data)
            await self.db.commit()
            return chunks
        except Exception as err:
            await self.db.rollback()
            raise DatabaseError(f"Failed to insert asset chunks: {str(err)}") from err

    async def search_similar_chunks(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query vector database for similar chunks using cosine similarity scoring."""
        try:
            return await self.chunk_repo.search_similar_chunks(query_vector, limit)
        except Exception as err:
            raise DatabaseError(f"Vector similarity search failed: {str(err)}") from err

    async def get_chunks_by_asset(self, asset_id: uuid.UUID) -> List[AssetChunk]:
        """Fetch all chunks related to an asset UUID."""
        try:
            return await self.chunk_repo.get_chunks_by_asset(asset_id)
        except Exception as err:
            raise DatabaseError(f"Failed to get chunks for asset: {str(err)}") from err
