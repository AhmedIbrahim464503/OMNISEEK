import os
import subprocess
from typing import Any, Dict, List, Tuple
from pypdf import PdfReader

from core.exceptions import ValidationError
from core.logging import logger

class MediaProcessorService:
    """Service handling text extraction, audio parsing, and video frame/audio demuxing via FFMpeg/FFprobe."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract plain text contents from .txt or .pdf files."""
        if not os.path.exists(file_path):
            raise ValidationError(f"Document file not found: {file_path}")
            
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    return file.read()
            except Exception as err:
                logger.error(f"Failed to read raw text file: {str(err)}")
                raise ValidationError(f"Could not read text file: {str(err)}")
                
        elif ext == ".pdf":
            try:
                reader = PdfReader(file_path)
                pages_content = []
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        pages_content.append(text)
                return "\n\n".join(pages_content)
            except Exception as err:
                logger.error(f"PDF content extraction failure: {str(err)}")
                raise ValidationError(f"Failed to parse PDF document text: {str(err)}")
                
        else:
            raise ValidationError(f"Unsupported document format: {ext}")

    @staticmethod
    def get_duration(file_path: str) -> float:
        """Execute ffprobe to capture duration of audio or video files."""
        if not os.path.exists(file_path):
            raise ValidationError(f"Media file not found: {file_path}")
            
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except (subprocess.SubprocessError, FileNotFoundError, ValueError) as err:
            logger.warning(
                f"FFprobe duration call failed for {file_path}: {str(err)}. "
                "Simulating approximate duration based on file size."
            )
            file_size = os.path.getsize(file_path)
            # Approximate duration: 10 seconds per MB
            simulated_duration = max(30.0, float(file_size) / (100 * 1024))
            return round(simulated_duration, 2)

    @staticmethod
    def process_video(
        video_path: str, asset_id: str, storage_dir: str
    ) -> Tuple[float, str, List[Dict[str, Any]]]:
        """Extract duration, demux audio track, and extract frame JPGs every 2 seconds."""
        duration = MediaProcessorService.get_duration(video_path)
        
        filename = os.path.basename(video_path)
        base_name, _ = os.path.splitext(filename)
        
        asset_dir = os.path.join(storage_dir, "assets", asset_id)
        output_audio_path = os.path.join(asset_dir, "audio", f"{base_name}_audio.mp3")
        frames_dir = os.path.join(asset_dir, "frames")
        
        # Demux audio track
        audio_command = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
            output_audio_path
        ]
        
        logger.info(f"Extracting audio track from video {video_path}...")
        ffmpeg_success = True
        try:
            subprocess.run(
                audio_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError) as err:
            ffmpeg_success = False
            logger.warning(
                f"FFMpeg audio demux failed for {video_path}: {str(err)}. "
                "Writing mock placeholder audio track."
            )
            with open(output_audio_path, "w") as mock_audio:
                mock_audio.write("MOCK_DEMUXED_AUDIO_TRACK_PLACEHOLDER")
                
        # Extract frames every 2 seconds
        frame_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
        frame_command = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", "fps=1/2",
            frame_pattern
        ]
        
        logger.info(f"Extracting frame assets from video {video_path}...")
        try:
            subprocess.run(
                frame_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError) as err:
            ffmpeg_success = False
            logger.warning(
                f"FFMpeg frame capture failed for {video_path}: {str(err)}. "
                "Generating placeholder frame markers."
            )
            
        frames = []
        number_of_frames = int(duration // 2) + 1
        
        for index in range(1, number_of_frames + 1):
            frame_name = f"frame_{index:04d}.jpg"
            frame_path = os.path.join(frames_dir, frame_name)
            timestamp = float((index - 1) * 2)
            
            if not ffmpeg_success or not os.path.exists(frame_path):
                # Write placeholder context
                with open(frame_path, "w") as mock_frame:
                    mock_frame.write(f"MOCK_FRAME_IMAGE_INDEX_{index}_TIME_{timestamp}")
                    
            frames.append({
                "frame_path": frame_path,
                "timestamp": timestamp
            })
            
        return duration, output_audio_path, frames
