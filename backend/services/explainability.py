from typing import Any, Dict

class ExplainabilityService:
    """Service to generate plain-text, human-readable rationales explaining why search results matched."""

    @staticmethod
    def generate_explanation(
        query: str,
        chunk: Dict[str, Any],
        strategy: str
    ) -> str:
        """
        Produce a descriptive sentence explaining why the document chunk matches the user query
        based on scores and retrieval strategy.
        """
        semantic_score = chunk.get("semantic_score", chunk.get("score", 0.0))
        keyword_score = chunk.get("keyword_score", 0.0)
        final_score = chunk.get("score", 0.0)
        modality = chunk.get("modality", "TEXT")
        asset_name = chunk.get("asset_name", "Unknown File")

        # Determine structural modality context
        modality_desc = {
            "TEXT": "text document content",
            "AUDIO": "audio spoken transcript segment",
            "VIDEO": "video segment"
        }.get(modality, "media segment")

        # Draft matching reasoning depending on the active retrieval path
        if strategy == "Fast (Vector Only)":
            reason = f"Highly relevant semantic match ({semantic_score:.2f} similarity) found in {modality_desc} for '{asset_name}'."
        elif strategy == "Balanced (Hybrid)":
            if semantic_score > 0.3 and keyword_score > 0.3:
                reason = f"Strong match containing both matching keywords (score: {keyword_score:.2f}) and contextual conceptual themes (score: {semantic_score:.2f}) inside '{asset_name}'."
            elif semantic_score > 0.3:
                reason = f"Conceptually matching segment (score: {semantic_score:.2f}) inside '{asset_name}' with high thematic relevance."
            else:
                reason = f"Keyword matching segment containing query terms (score: {keyword_score:.2f}) inside '{asset_name}'."
        elif strategy == "Accurate (Hybrid + Reranked)":
            vector_score = chunk.get("vector_score", semantic_score)
            reason = f"Cross-Encoder reranked match (refined score: {final_score:.2f}, initial vector score: {vector_score:.2f}) verified against query terms inside '{asset_name}'."
        else:
            reason = f"Matched search candidate in '{asset_name}' with score: {final_score:.2f}."

        return reason
