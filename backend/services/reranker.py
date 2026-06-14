import numpy as np
from typing import Any, Dict, List
from services.ai_model_manager import AIModelManager
from core.logging import logger

class RerankerService:
    """Service utilizing Cross-Encoder models to re-evaluate and refine semantic matching scores."""

    @staticmethod
    def rerank_candidates(
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunks against a query using local Cross-Encoder BAAI/bge-reranker-base.
        Uses batch processing and returns the top-k sorted items.
        """
        if not query or not candidates:
            return candidates[:top_k]

        try:
            model_manager = AIModelManager()
            model = model_manager.reranker_model

            # Form list of (query, content) pairs for batch cross-encoder prediction
            pairs = [(query, c["content"]) for c in candidates]
            
            # Compute cross-encoder scores (raw logits)
            raw_scores = model.predict(pairs, batch_size=32, convert_to_numpy=True)

            # Map raw logits to [0.0, 1.0] range using sigmoid normalization
            normalized_scores = 1.0 / (1.0 + np.exp(-raw_scores))

            # Update scores in-place on copies
            reranked_results = []
            for idx, candidate in enumerate(candidates):
                updated_cand = dict(candidate)
                # Keep record of original vector retrieval score, and assign new reranked score
                updated_cand["vector_score"] = candidate.get("score", 0.0)
                updated_cand["score"] = float(normalized_scores[idx])
                reranked_results.append(updated_cand)

            # Sort by new reranking score in descending order
            reranked_results.sort(key=lambda x: x["score"], reverse=True)

            return reranked_results[:top_k]

        except Exception as e:
            logger.error(f"Error executing cross-encoder reranking: {str(e)}")
            # Fallback gracefully to vector search scores if reranker fails
            for c in candidates:
                c["vector_score"] = c.get("score", 0.0)
            return candidates[:top_k]
