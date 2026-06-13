import os
from typing import Any, Dict, List
from services.ai_model_manager import AIModelManager
from services.text_embedding import TextEmbeddingService
from core.logging import logger
from core.exceptions import ValidationError

class AudioEmbeddingService:
    """Service wrapping Whisper transcription and BGE-M3 text embeddings for audio tracks."""

    @staticmethod
    def process_audio(audio_path: str) -> List[Dict[str, Any]]:
        """Transcribe audio tracks using Whisper and encode segments using BGE-M3."""
        if not os.path.exists(audio_path):
            raise ValidationError(f"Audio file target not found: {audio_path}")
            
        model_manager = AIModelManager()
        whisper = model_manager.whisper_model
        
        logger.info(f"Invoking Faster-Whisper local inference on path: {audio_path}...")
        
        # Transcribe audio track with word/segment boundary timestamps
        try:
            segments, info = whisper.transcribe(audio_path, beam_size=5)
            # materializing generator to list
            segment_list = list(segments)
        except Exception as err:
            logger.error(f"Whisper transcription execution failed: {str(err)}")
            raise ValidationError(f"Whisper inference error: {str(err)}")
            
        results = []
        for idx, segment in enumerate(segment_list):
            segment_text = segment.text.strip()
            if not segment_text:
                continue
                
            logger.info(
                f"Transcribed Audio Chunk [{segment.start:.2f}s -> {segment.end:.2f}s]: "
                f"\"{segment_text}\""
            )
            
            # Embed transcribed segment text
            embedding = TextEmbeddingService.embed_text(segment_text)
            
            results.append({
                "chunk_index": idx,
                "content": segment_text,
                "start_time": float(segment.start),
                "end_time": float(segment.end),
                "embedding": embedding,
                "metadata": {
                    "avg_logprob": float(segment.avg_logprob),
                    "no_speech_prob": float(segment.no_speech_prob)
                }
            })
            
        return results
