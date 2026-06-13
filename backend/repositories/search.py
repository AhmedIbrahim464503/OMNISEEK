import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset, ModalityEnum
from models.chunk import AssetChunk

class SemanticSearchRepository:
    """Repository carrying out vector similarity queries against chunk and asset tables."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search_similar_chunks(
        self,
        query_vector: List[float],
        limit: int = 20,
        modality: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector database for similar chunks using cosine distance operator.
        Joins chunk record with the parent asset.
        Supports filtering by modality.
        """
        # distance operator (mapped to <=> operator of pgvector)
        distance = AssetChunk.embedding.cosine_distance(query_vector)
        
        stmt = (
            select(
                AssetChunk.id.label("chunk_id"),
                AssetChunk.asset_id,
                Asset.filename.label("asset_name"),
                Asset.modality,
                AssetChunk.chunk_index,
                AssetChunk.content,
                AssetChunk.start_time,
                AssetChunk.end_time,
                (1.0 - distance).label("similarity_score")
            )
            .join(Asset, AssetChunk.asset_id == Asset.id)
        )
        
        # If modality filter is provided, validate and apply it
        if modality:
            try:
                modality_enum = ModalityEnum(modality.upper())
                stmt = stmt.filter(Asset.modality == modality_enum)
            except ValueError:
                # If invalid modality enum value is passed, return empty or ignore
                return []

        # Exclude chunks with null embeddings
        stmt = stmt.filter(AssetChunk.embedding.isnot(None))

        # Order by similarity (smallest distance first)
        stmt = stmt.order_by(distance.asc()).limit(limit)
        
        result = await self.db.execute(stmt)
        
        return [
            {
                "chunk_id": row.chunk_id,
                "asset_id": str(row.asset_id),
                "asset_name": row.asset_name,
                "modality": row.modality.value if hasattr(row.modality, "value") else str(row.modality),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "score": float(row.similarity_score) if row.similarity_score is not None else 0.0
            }
            for row in result.all()
        ]
