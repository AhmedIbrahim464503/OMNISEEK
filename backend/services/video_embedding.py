import os
import numpy as np
import torch
from PIL import Image
from typing import Any, Dict, List

from core.logging import logger
from services.ai_model_manager import AIModelManager
from services.audio_embedding import AudioEmbeddingService

class VideoEmbeddingService:
    """Service wrapping CLIP image extraction and audio transcription for video analysis."""

    @staticmethod
    def embed_frame(image_path: str) -> List[float]:
        """Convert a frame JPG image into a 512-dimensional L2-normalized CLIP embedding vector."""
        if not os.path.exists(image_path):
            logger.warning(f"Frame image target not found: {image_path}. Returning default vector.")
            return [0.0] * 512
            
        model_manager = AIModelManager()
        model = model_manager.clip_model
        processor = model_manager.clip_processor
        
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")
            
            with torch.no_grad():
                features = model.get_image_features(**inputs)
                
            embedding_np = features[0].cpu().numpy()
            
            # L2 normalize the CLIP output representation
            norm = np.linalg.norm(embedding_np)
            if norm > 0:
                embedding_np = embedding_np / norm
                
            return embedding_np.tolist()
        except Exception as err:
            logger.error(f"Failed to generate CLIP embedding for {image_path}: {str(err)}")
            # Fail-safe fallback: return zero vector
            return [0.0] * 512

    @staticmethod
    def process_video_audio(audio_path: str) -> List[Dict[str, Any]]:
        """Transcribe and embed audio files using Whisper transcription + BGE-M3 text encoding."""
        return AudioEmbeddingService.process_audio(audio_path)
