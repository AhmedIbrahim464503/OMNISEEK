import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.logging import logger
from repositories.search import SemanticSearchRepository
from services.search_embedding import SearchEmbeddingService
from services.search_analytics import SearchAnalyticsService

class ScoreNormalizer:
    """Normalize raw cosine similarity scores into a strict 0.0 to 1.0 confidence range."""

    @staticmethod
    def normalize_score(score: float) -> float:
        # Map raw cosine similarity [-1.0, 1.0] to [0.0, 1.0]
        normalized = (score + 1.0) / 2.0
        return max(0.0, min(1.0, normalized))

class DuplicateResultFilter:
    """Filters duplicate chunks by keeping the entry with the highest score."""

    @staticmethod
    def filter_duplicates(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique_chunks = {}
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            score = chunk.get("score", 0.0)
            if chunk_id not in unique_chunks or score > unique_chunks[chunk_id]["score"]:
                unique_chunks[chunk_id] = chunk
        return list(unique_chunks.values())

class ResultAggregator:
    """Aggregates search results, merging duplicates and adjacent temporal segments."""

    @staticmethod
    def aggregate(
        chunks: List[Dict[str, Any]],
        quality_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        # Deduplicate identical chunks
        chunks = DuplicateResultFilter.filter_duplicates(chunks)

        # Group by asset to merge adjacent chunk indices
        by_asset: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in chunks:
            asset_id = chunk["asset_id"]
            if asset_id not in by_asset:
                by_asset[asset_id] = []
            by_asset[asset_id].append(chunk)

        aggregated = []
        for asset_id, asset_chunks in by_asset.items():
            # Sort chronologically by chunk index
            asset_chunks.sort(key=lambda x: x["chunk_index"])

            merged: List[Dict[str, Any]] = []
            for chunk in asset_chunks:
                if not merged:
                    merged.append(dict(chunk))
                    continue

                last = merged[-1]
                # Adjacent indices (difference of 0 or 1) are merged into one temporal segment
                if chunk["chunk_index"] - last["chunk_index"] <= 1:
                    last["content"] = (last["content"].strip() + " " + chunk["content"].strip()).strip()
                    
                    if last["start_time"] is not None and chunk["start_time"] is not None:
                        last["start_time"] = min(last["start_time"], chunk["start_time"])
                    elif chunk["start_time"] is not None:
                        last["start_time"] = chunk["start_time"]

                    if last["end_time"] is not None and chunk["end_time"] is not None:
                        last["end_time"] = max(last["end_time"], chunk["end_time"])
                    elif chunk["end_time"] is not None:
                        last["end_time"] = chunk["end_time"]

                    last["score"] = max(last["score"], chunk["score"])
                    last["chunk_index"] = chunk["chunk_index"]
                else:
                    merged.append(dict(chunk))
            aggregated.extend(merged)

        # Remove low quality matches
        final_results = []
        for item in aggregated:
            if item["score"] >= quality_threshold:
                final_results.append({
                    "asset_id": item["asset_id"],
                    "asset_name": item["asset_name"],
                    "modality": item["modality"],
                    "content": item["content"],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"],
                    "score": round(item["score"], 4)
                })

        # Sort descending by score
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results

class SearchService:
    """Orchestrator coordinating semantic embedding creation, similarity retrieval, result formatting, and analytics telemetry."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = SemanticSearchRepository(db)
        self.analytics_service = SearchAnalyticsService(db)

    async def execute_search(
        self,
        query: str,
        limit: int = 20,
        modality: Optional[str] = None,
        quality_threshold: float = 0.0
    ) -> Dict[str, Any]:
        """
        Runs the semantic search workflow:
        1. Generates the query embedding using BGE-M3.
        2. Retrieves candidate chunks from pgvector.
        3. Normalizes similarity scores.
        4. Aggregates neighboring chunks and filters duplicates.
        5. Logs metrics to console and db analytics.
        """
        start_time = time.perf_counter()
        
        if not query.strip():
            return {
                "query": query,
                "count": 0,
                "results": []
            }

        try:
            # Generate query embedding
            query_vector = SearchEmbeddingService.generate_query_embedding(query)
            
            # Retrieve similar candidates
            candidates = await self.repository.search_similar_chunks(
                query_vector=query_vector,
                limit=limit,
                modality=modality
            )
            candidate_count = len(candidates)

            # Normalize scores in-place
            for c in candidates:
                c["score"] = ScoreNormalizer.normalize_score(c["score"])

            # Aggregate and format
            results = ResultAggregator.aggregate(candidates, quality_threshold=quality_threshold)
            final_count = len(results)
            top_score = results[0]["score"] if results else 0.0

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Log execution details locally
            logger.info(
                f"Semantic Search Complete: query='{query}', modality={modality}, "
                f"latency={latency_ms:.2f}ms, candidates={candidate_count}, "
                f"results={final_count}, top_score={top_score:.4f}"
            )

            # Persist search analytics to DB (async logging)
            try:
                await self.analytics_service.log_search(
                    query=query,
                    latency_ms=latency_ms,
                    results_count=final_count
                )
            except Exception as e:
                logger.error(f"Failed to record search log to database: {str(e)}")

            return {
                "query": query,
                "count": final_count,
                "results": results
            }

        except Exception as err:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"Semantic Search Failure: query='{query}', modality={modality}, "
                f"latency={latency_ms:.2f}ms, error='{str(err)}'"
            )
            raise err
