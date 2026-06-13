from typing import Any, Dict, List

class ChunkingService:
    """Service handling multi-modal media chunking strategies for text, audio, and video formats."""

    @staticmethod
    def chunk_text(text: str) -> List[Dict[str, Any]]:
        """Slice document text content into 500-character blocks with 50-character overlaps."""
        if not text:
            return []
            
        chunks = []
        chunk_size = 500
        overlap = 50
        step = chunk_size - overlap
        
        chunk_index = 0
        start_pos = 0
        
        while start_pos < len(text):
            chunk_content = text[start_pos:start_pos + chunk_size].strip()
            if chunk_content:
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": chunk_content,
                    "start_time": None,
                    "end_time": None,
                    "metadata": {"char_length": len(chunk_content)}
                })
                chunk_index += 1
            # Prevent infinite loops when the remaining text is smaller than step
            if start_pos + chunk_size >= len(text):
                break
            start_pos += step
            
        return chunks

    @staticmethod
    def chunk_audio(duration: float) -> List[Dict[str, Any]]:
        """Slice audio duration timeline into standard 30-second chunk blocks."""
        chunks = []
        chunk_interval = 30.0
        
        chunk_index = 0
        start_time = 0.0
        while start_time < duration:
            end_time = min(start_time + chunk_interval, duration)
            chunks.append({
                "chunk_index": chunk_index,
                "content": f"[Audio Chunk Placeholder: {start_time:.1f}s - {end_time:.1f}s]",
                "start_time": start_time,
                "end_time": end_time,
                "metadata": {"transcript_placeholder": True}
            })
            chunk_index += 1
            start_time = end_time
            
        return chunks

    @staticmethod
    def chunk_video(duration: float, frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Slice video timeline into 2-second chunks, matching extracted frames inside."""
        chunks = []
        chunk_interval = 2.0
        
        chunk_index = 0
        start_time = 0.0
        while start_time < duration:
            end_time = min(start_time + chunk_interval, duration)
            
            # Match frame objects within temporal boundary
            matched_frames = [
                frame for frame in frames if start_time <= frame["timestamp"] <= end_time
            ]
            
            chunks.append({
                "chunk_index": chunk_index,
                "content": f"[Video Chunk Placeholder: {start_time:.1f}s - {end_time:.1f}s]",
                "start_time": start_time,
                "end_time": end_time,
                "metadata": {
                    "frames": matched_frames,
                    "frame_count": len(matched_frames)
                }
            })
            chunk_index += 1
            start_time = end_time
            
        return chunks
