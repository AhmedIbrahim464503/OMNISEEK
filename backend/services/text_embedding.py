import numpy as np
from typing import List
from services.ai_model_manager import AIModelManager

class TextEmbeddingService:
    """Service wrapping BAAI/bge-m3 sentence transformer execution for text chunk embeddings."""

    @staticmethod
    def embed_text(text: str) -> List[float]:
        """Convert text into a 512-dimensional L2-normalized embedding representation."""
        if not text:
            # Handle empty strings with a default zero vector
            return [0.0] * 512
            
        model_manager = AIModelManager()
        model = model_manager.bge_m3_model
        
        # Compute dense embeddings from sentence-transformers
        embedding_1024 = model.encode(text, convert_to_numpy=True)
        
        # Truncate to first 512 dimensions to conform to pgvector schema constraints
        embedding_512 = embedding_1024[:512]
        
        # Perform L2 normalization on the truncated representation
        norm = np.linalg.norm(embedding_512)
        if norm > 0:
            embedding_512 = embedding_512 / norm
            
        return embedding_512.tolist()
