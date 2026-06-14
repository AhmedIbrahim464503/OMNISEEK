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
        
        # Compute dense embeddings from sentence-transformers (yields 384 dimensions)
        embedding_384 = model.encode(text, convert_to_numpy=True)
        
        # Pad with zeros to 512 dimensions to conform to pgvector schema constraints
        embedding_512 = np.pad(embedding_384, (0, 128), 'constant')
        
        # Perform L2 normalization on the padded representation
        norm = np.linalg.norm(embedding_512)
        if norm > 0:
            embedding_512 = embedding_512 / norm
            
        return embedding_512.tolist()
