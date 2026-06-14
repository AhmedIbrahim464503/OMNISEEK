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
            
            # Generate raw dense embedding (384 dimensions for all-MiniLM-L6-v2)
            embedding_384 = model.encode(query, convert_to_numpy=True)
            
            # Pad with zeros to 512 dimensions to conform to pgvector schema constraints
            embedding_512 = np.pad(embedding_384, (0, 128), 'constant')
            
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
