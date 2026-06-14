import asyncio
from typing import Any, Dict, List, Optional
from repositories.search import SemanticSearchRepository

class HybridSearchService:
    """Service combining vector semantic search and full-text keyword search using weighted fusion."""

    def __init__(self, repository: SemanticSearchRepository) -> None:
        self.repository = repository

    async def execute_hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        limit: int = 50,
        modality: Optional[str] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieves candidates from both vector search and FTS keyword search,
        then merges candidates using a weighted score fusion formula.
        """
        # Run both searches in parallel using asyncio.gather for optimal latency
        vector_task = self.repository.search_similar_chunks(
            query_vector=query_vector,
            limit=limit,
            modality=modality
        )
        keyword_task = self.repository.search_keyword_chunks(
            query_text=query_text,
            limit=limit,
            modality=modality
        )

        vector_results, keyword_results = await asyncio.gather(vector_task, keyword_task)

        # Merge candidate pools
        merged_candidates: Dict[Any, Dict[str, Any]] = {}

        # 1. Process vector candidates. Set initial scores.
        for item in vector_results:
            chunk_id = item["chunk_id"]
            merged_candidates[chunk_id] = {
                "chunk_id": item["chunk_id"],
                "asset_id": item["asset_id"],
                "asset_name": item["asset_name"],
                "modality": item["modality"],
                "chunk_index": item["chunk_index"],
                "content": item["content"],
                "start_time": item.get("start_time"),
                "end_time": item.get("end_time"),
                "semantic_score": item["score"],
                "keyword_score": 0.0
            }

        # 2. Process keyword candidates. Merge scores if they already exist, otherwise add.
        for item in keyword_results:
            chunk_id = item["chunk_id"]
            if chunk_id in merged_candidates:
                merged_candidates[chunk_id]["keyword_score"] = item["score"]
            else:
                # Keyword-only matches are assigned a default semantic score of 0.0
                merged_candidates[chunk_id] = {
                    "chunk_id": item["chunk_id"],
                    "asset_id": item["asset_id"],
                    "asset_name": item["asset_name"],
                    "modality": item["modality"],
                    "chunk_index": item["chunk_index"],
                    "content": item["content"],
                    "start_time": item.get("start_time"),
                    "end_time": item.get("end_time"),
                    "semantic_score": 0.0,
                    "keyword_score": item["score"]
                }

        # 3. Apply weighted fusion formula
        fused_results = []
        for chunk_id, cand in merged_candidates.items():
            fused_score = (cand["semantic_score"] * semantic_weight) + (cand["keyword_score"] * keyword_weight)
            cand["score"] = fused_score
            fused_results.append(cand)

        # Sort descending by fused score
        fused_results.sort(key=lambda x: x["score"], reverse=True)

        return fused_results[:limit]
