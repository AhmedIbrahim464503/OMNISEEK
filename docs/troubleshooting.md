# Troubleshooting Guide

This document outlines common runtime issues, failure diagnostics, and step-by-step procedures for resolution.

---

## 1. Media Processing Issues

### FFMpeg/FFprobe Subprocess Failures
*   **Symptom**: Logs display warning messages like: `FFMpeg audio demux failed for ...` or `FFprobe duration call failed ...`.
*   **Cause**: The local development machine (when running outside the Docker container) lacks `ffmpeg` or `ffprobe` binaries in its system path.
*   **Resolution**:
    1.  Verify that you are running executions inside the Docker container stack via `docker-compose exec`, which includes these dependencies natively.
    2.  If executing bare-metal tests, install FFmpeg on your host machine (e.g., via `choco install ffmpeg` on Windows, or `brew install ffmpeg` on macOS) and append it to your system PATH.
    *   *Note*: The service implements graceful fallback, writing dummy placeholder files so it will not crash.

---

## 2. Ingestion Failures

### 400 Bad Request: Unsupported Extensions
*   **Symptom**: Upload returns a `400` validation error message.
*   **Cause**: The uploaded file has an extension not listed in `SUPPORTED_EXTENSIONS`.
*   **Resolution**: Ensure file suffixes match the supported set: `.txt`, `.pdf`, `.mp3`, `.wav`, `.mp4`, or `.mov`.

### Directory Permissions Errors
*   **Symptom**: `Failed to write file stream to storage: [Errno 13] Permission denied`.
*   **Cause**: The application cannot write to the mapped `/storage` host directory.
*   **Resolution**: Adjust permissions on the local directory folder mapped to the `./storage` container volume to allow write access for container processes.
