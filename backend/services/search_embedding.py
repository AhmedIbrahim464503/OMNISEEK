import numpy as np
from typing import List
from services.ai_model_manager import AIModelManager
from core.logging import logger

class SearchEmbeddingService:
    """Service for generating BGE-M3 query embeddings, conforming to database dimensional constraints."""

    @staticmethod
    def generate_query_embedding(query: str, normalize: bool = True) -> List[float]:
        """
        Accept query string and generate the 512-dimensional vector.
        Reuses the existing AIModelManager model.
        """
        if not query:
            return [0.0] * 512

        try:
            model_manager = AIModelManager()
            model = model_manager.bge_m3_model
            
            # Generate raw dense embedding (1024 dimensions for BGE-M3)
            embedding_1024 = model.encode(query, convert_to_numpy=True)
            
            # Truncate/slice to 512 dimensions to match the asset_chunks.embedding constraint
            embedding_512 = embedding_1024[:512]
            
            # Normalize vector if required (cosine similarity requires normalized vectors)
            if normalize:
                norm = np.linalg.norm(embedding_512)
                if norm > 0:
                    embedding_512 = embedding_512 / norm
            
            # Validate output dimension
            if len(embedding_512) != 512:
                logger.error(f"Embedding validation failed: generated dimension is {len(embedding_512)}, expected 512.")
                raise ValueError(f"Expected 512-dimensional vector, got {len(embedding_512)}")
                
            return embedding_512.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise e
