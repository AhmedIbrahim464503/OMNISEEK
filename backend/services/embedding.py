from typing import List
from services.text_embedding import TextEmbeddingService
from services.video_embedding import VideoEmbeddingService

class EmbeddingService:
    """High-level service orchestrating BGE-M3 text and CLIP image embedding generation."""

    @staticmethod
    def embed_text(text: str) -> List[float]:
        """Generate a 512-dimensional normalized embedding for text content."""
        vector = TextEmbeddingService.embed_text(text)
        if len(vector) != 512:
            raise ValueError(f"Vector validation error: expected 512 dims, got {len(vector)}.")
        return vector

    @staticmethod
    def embed_image(image_path: str) -> List[float]:
        """Generate a 512-dimensional normalized embedding for visual frame JPGs."""
        vector = VideoEmbeddingService.embed_frame(image_path)
        if len(vector) != 512:
            raise ValueError(f"Vector validation error: expected 512 dims, got {len(vector)}.")
        return vector
