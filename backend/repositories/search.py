import uuid
import math
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset, ModalityEnum
from models.chunk import AssetChunk

class SemanticSearchRepository:
    """Repository carrying out vector similarity and full-text keyword queries against chunk and asset tables."""

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
        
        if modality:
            try:
                modality_enum = ModalityEnum(modality.upper())
                stmt = stmt.filter(Asset.modality == modality_enum)
            except ValueError:
                return []

        # Exclude chunks with null embeddings
        stmt = stmt.filter(AssetChunk.embedding.isnot(None))

        # Order by similarity (smallest distance first)
        stmt = stmt.order_by(distance.asc()).limit(limit)
        
        result = await self.db.execute(stmt)
        
        results = []
        for row in result.all():
            raw_score = float(row.similarity_score) if row.similarity_score is not None else -1.0
            if math.isnan(raw_score):
                raw_score = -1.0
            
            results.append({
                "chunk_id": row.chunk_id,
                "asset_id": str(row.asset_id),
                "asset_name": row.asset_name,
                "modality": row.modality.value if hasattr(row.modality, "value") else str(row.modality),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "score": raw_score
            })
        return results

    async def search_keyword_chunks(
        self,
        query_text: str,
        limit: int = 20,
        modality: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query database for chunks matching the query string using PostgreSQL Full-Text Search.
        Calculates relevance score using ts_rank and joins chunk with parent asset.
        """
        if not query_text.strip():
            return []

        # Parse query using plainto_tsquery (splits by whitespace and acts as AND)
        fts_query = func.plainto_tsquery("english", query_text)
        fts_vector = func.to_tsvector("english", AssetChunk.content)
        rank = func.ts_rank(fts_vector, fts_query)

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
                rank.label("fts_rank")
            )
            .join(Asset, AssetChunk.asset_id == Asset.id)
            .filter(fts_vector.op("@@")(fts_query))
        )

        if modality:
            try:
                modality_enum = ModalityEnum(modality.upper())
                stmt = stmt.filter(Asset.modality == modality_enum)
            except ValueError:
                return []

        # Order by rank descending
        stmt = stmt.order_by(rank.desc()).limit(limit)

        result = await self.db.execute(stmt)

        results = []
        for row in result.all():
            raw_rank = float(row.fts_rank) if row.fts_rank is not None else 0.0
            # Normalize ts_rank to [0.0, 1.0] using soft saturation curve: rank / (rank + 1.0)
            normalized_score = raw_rank / (raw_rank + 1.0) if raw_rank > 0.0 else 0.0
            
            results.append({
                "chunk_id": row.chunk_id,
                "asset_id": str(row.asset_id),
                "asset_name": row.asset_name,
                "modality": row.modality.value if hasattr(row.modality, "value") else str(row.modality),
                "chunk_index": row.chunk_index,
                "content": row.content,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "score": normalized_score
            })
        return results
