# Media Processing & Extractor Specifications

This document catalogs the technical setup, subprocess calls, and external binaries used by the extraction layer to parse text, audio, and video files.

---

## 1. Document Extraction (PDF & TXT)

*   **TXT Files**: Content is read directly from local disk via Python's standard `open()` using the `utf-8` encoder with safety exception handlers.
*   **PDF Files**: Text is parsed page-by-page asynchronously using `pypdf.PdfReader`. Extracted string blocks are joined with double-newlines.

---

## 2. Audio Processing (FFprobe)

To determine timeline boundaries for temporal indexing, the backend calls the `ffprobe` command via Python's `subprocess` module:
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {media_file_path}
```
*   **Failure Fallback**: If the command fails, or if `ffprobe` is not installed on the system, the service estimates the duration based on file size (assuming standard audio stream bitrates) to prevent application execution blocks.

---

## 3. Video Processing (FFmpeg Demuxing)

For every uploaded video asset (`.mp4`, `.mov`), the processor carries out two distinct subprocess actions:

1.  **Audio Track Extraction**: Demuxes the video file to isolate the audio channel as an MP3 track:
    ```bash
    ffmpeg -y -i {video_path} -vn -acodec libmp3lame -q:a 2 {output_audio_path}
    ```
2.  **Frame Capture**: Slices the video visually, saving frame images in JPG format every 2 seconds:
    ```bash
    ffmpeg -y -i {video_path} -vf fps=1/2 {frames_directory}/frame_%04d.jpg
    ```

*   **Mock Fallbacks**: If `ffmpeg` or `ffprobe` binaries are missing from the PATH, the processor logs a warning and creates placeholder dummy files inside the `/storage` subdirectory.
