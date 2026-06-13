import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset
from models.chunk import AssetChunk
from repositories.base import BaseRepository

class ChunkRepository(BaseRepository[AssetChunk]):
    """Repository implementation for database access operations on the AssetChunk model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the repository binding it to the AssetChunk model and DB session."""
        super().__init__(AssetChunk, db)

    async def insert_chunks_bulk(self, chunks_data: List[Dict[str, Any]]) -> List[AssetChunk]:
        """Bulk insert multiple AssetChunk entities into the database session."""
        chunks = [
            AssetChunk(
                asset_id=data["asset_id"],
                chunk_index=data["chunk_index"],
                content=data["content"],
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                metadata=data.get("metadata", {}),
                embedding=data["embedding"]
            )
            for data in chunks_data
        ]
        self.db.add_all(chunks)
        return chunks

    async def search_similar_chunks(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query vector database for similar chunks using cosine distance operator."""
        distance = AssetChunk.embedding.cosine_distance(query_vector)
        stmt = (
            select(
                Asset.filename.label("asset_name"),
                Asset.file_path,
                AssetChunk.content.label("chunk_content"),
                AssetChunk.start_time,
                AssetChunk.end_time,
                (1.0 - distance).label("similarity_score")
            )
            .join(Asset, AssetChunk.asset_id == Asset.id)
            .order_by(distance.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "asset_name": row.asset_name,
                "file_path": row.file_path,
                "chunk_content": row.chunk_content,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "similarity_score": float(row.similarity_score)
            }
            for row in result.all()
        ]

    async def get_chunks_by_asset(self, asset_id: uuid.UUID) -> List[AssetChunk]:
        """Fetch all AssetChunk records associated with a parent Asset UUID."""
        stmt = (
            select(AssetChunk)
            .filter(AssetChunk.asset_id == asset_id)
            .order_by(AssetChunk.chunk_index.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
