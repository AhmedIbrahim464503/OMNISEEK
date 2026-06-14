import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.logging import logger
from repositories.search import SemanticSearchRepository
from services.search_embedding import SearchEmbeddingService
from services.search_analytics import SearchAnalyticsService
from services.cache import CacheService
from api.metrics import metrics_collector

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
                    "score": round(item["score"], 4),
                    "semantic_score": round(item.get("semantic_score", item.get("score", 0.0)), 4),
                    "keyword_score": round(item.get("keyword_score", 0.0), 4),
                    "vector_score": round(item.get("vector_score", item.get("semantic_score", item.get("score", 0.0))), 4)
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
        mode: str = "fast",
        minimum_score: float = 0.30
    ) -> Dict[str, Any]:
        """
        Runs the search workflow according to execution profiles:
        1. Fast: Vector search only.
        2. Balanced: FTS + Vector hybrid search.
        3. Accurate: FTS + Vector + Cross-Encoder reranker.
        """
        start_time = time.perf_counter()
        
        if not query.strip():
            return {
                "query": query,
                "strategy": "Unknown",
                "count": 0,
                "latency": {"total_ms": 0.0},
                "results": []
            }

        # Cache check
        cache_key = f"search:{query}:{modality}:{mode}:{limit}:{minimum_score}"
        try:
            cached_data = await CacheService.get(cache_key)
            if cached_data is not None:
                total_ms = (time.perf_counter() - start_time) * 1000.0
                metrics_collector.record_search(mode, total_ms / 1000.0)
                return cached_data
        except Exception as err:
            logger.warning(f"Search cache bypass: {str(err)}")

        try:
            # 1. Generate query embedding
            embed_start = time.perf_counter()
            query_vector = SearchEmbeddingService.generate_query_embedding(query)
            embed_ms = (time.perf_counter() - embed_start) * 1000.0

            # 2. Retrieve candidates
            retrieval_start = time.perf_counter()
            
            # Larger retrieval pool limit for Reranking pipeline
            retrieval_pool_limit = 50 if mode == "accurate" else limit

            if mode == "fast":
                candidates = await self.repository.search_similar_chunks(
                    query_vector=query_vector,
                    limit=retrieval_pool_limit,
                    modality=modality
                )
                for c in candidates:
                    # Normalize scores to [0.0, 1.0] for consistent threshold comparisons
                    c["score"] = ScoreNormalizer.normalize_score(c["score"])
                    c["semantic_score"] = c["score"]
                    c["keyword_score"] = 0.0
                    c["vector_score"] = c["score"]
            else:
                # Balanced or Accurate uses Hybrid search fusion
                from services.hybrid_search import HybridSearchService
                hybrid_service = HybridSearchService(self.repository)
                candidates = await hybrid_service.execute_hybrid_search(
                    query_text=query,
                    query_vector=query_vector,
                    limit=retrieval_pool_limit,
                    modality=modality
                )
                
            retrieval_ms = (time.perf_counter() - retrieval_start) * 1000.0

            # 3. Rerank if in Accurate Mode
            rerank_start = time.perf_counter()
            if mode == "accurate" and candidates:
                from services.reranker import RerankerService
                candidates = RerankerService.rerank_candidates(
                    query=query,
                    candidates=candidates,
                    top_k=limit
                )
            rerank_ms = (time.perf_counter() - rerank_start) * 1000.0

            # 4. Result Aggregation (merges adjacent chunks)
            aggregated_results = ResultAggregator.aggregate(candidates, quality_threshold=0.0)

            # 5. Apply ResultQualityFilter (threshold + near-duplicates check)
            from services.quality_filter import ResultQualityFilter
            final_results = ResultQualityFilter.filter_results(
                aggregated_results,
                minimum_score=minimum_score
            )

            # 6. Generate Match Reasons via ExplainabilityService
            strategy = {
                "fast": "Fast (Vector Only)",
                "balanced": "Balanced (Hybrid)",
                "accurate": "Accurate (Hybrid + Reranked)"
            }.get(mode.lower(), "Custom Strategy")

            from services.explainability import ExplainabilityService
            for item in final_results:
                item["reason"] = ExplainabilityService.generate_explanation(
                    query=query,
                    chunk=item,
                    strategy=strategy
                )

            total_ms = (time.perf_counter() - start_time) * 1000.0

            # Save Search Telemetry Log (F5 table)
            try:
                await self.analytics_service.log_search(
                    query=query,
                    latency_ms=total_ms,
                    results_count=len(final_results)
                )
            except Exception as e:
                logger.error(f"F5 analytics log failed: {e}")

            # Save Performance Latency Log (F6 table)
            try:
                from models.performance_log import SearchPerformanceLog
                perf_log = SearchPerformanceLog(
                    query=query,
                    retrieval_ms=retrieval_ms,
                    rerank_ms=rerank_ms,
                    total_ms=total_ms
                )
                self.db.add(perf_log)
                await self.db.commit()
            except Exception as e:
                logger.error(f"F6 performance log failed: {e}")
                await self.db.rollback()

            # Record Prometheus metrics
            metrics_collector.record_db(retrieval_ms / 1000.0)
            metrics_collector.record_search(mode, total_ms / 1000.0)

            response_payload = {
                "query": query,
                "strategy": strategy,
                "count": len(final_results),
                "latency": {
                    "embedding_ms": round(embed_ms, 2),
                    "retrieval_ms": round(retrieval_ms, 2),
                    "rerank_ms": round(rerank_ms, 2),
                    "total_ms": round(total_ms, 2)
                },
                "results": final_results
            }
            
            try:
                await CacheService.set(cache_key, response_payload, ttl=300)
            except Exception as err:
                logger.warning(f"Search cache write error: {str(err)}")

            return response_payload

        except Exception as err:
            total_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                f"Semantic Search Failure: query='{query}', modality={modality}, "
                f"latency={total_ms:.2f}ms, error='{str(err)}'"
            )
            raise err
