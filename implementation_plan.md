# Phase 3: File Ingestion Pipeline, Preprocessing, and Metadata Generation

Build and implement the core file ingestion pipeline. This pipeline will accept uploads (.txt, .pdf, .mp3, .wav, .mp4, .mov), execute local file persistence with multi-directory isolation, run raw media structural extractions (text extraction, FFprobe duration parsing, FFMpeg frame/audio parsing), segment metadata temporally, and commit chunks into the Postgres database.

## User Review Required

> [!IMPORTANT]
> The processing pipeline will run **synchronously** in Phase 3 for validation purposes.
>
> We will add `pypdf` dependency for parsing text from PDF documents.
>
> FFMpeg/FFprobe subprocess executions are invoked to extract frame timestamps and audio tracks. To make the code highly resilient in local non-container tests, the code gracefully catches command failures or missing binaries, logging warning messages and generating realistic placeholders instead of crashing.
>
> The storage system creates directories at `/storage/assets/{asset_id}/` (with subdirectories `raw/`, `frames/`, `audio/`, and `processed/`). We make the base storage directory customizable in `Settings` (defaulting to `./storage`).

## Open Questions

There are no unresolved open questions. The file types, directories, chunking logic (500-char with 50-overlap text chunks, 30s audio chunks, and 2s video frames/audio mappings) are fully defined.

## Proposed Changes

### Configuration Updates

#### [MODIFY] [config.py](file:///d:/projects/sps_project/backend/core/config.py)
Add a configurable setting parameter `STORAGE_DIR` (defaulting to `"./storage"`).

#### [MODIFY] [requirements.txt](file:///d:/projects/sps_project/backend/requirements.txt)
Append `pypdf>=4.0.0` and `python-multipart>=0.0.9` (required for FastAPI UploadFile parameters).

---

### Service Layer Implementations

#### [NEW] [upload.py](file:///d:/projects/sps_project/backend/services/upload.py)
Implements `UploadService` validating file formats, creating subdirectories under `STORAGE_DIR/assets/{asset_id}/` (`raw/`, `frames/`, `audio/`, `processed/`), writing file streams, and writing the database model.

#### [NEW] [media_processor.py](file:///d:/projects/sps_project/backend/services/media_processor.py)
Implements `MediaProcessorService` calling `pypdf` for documents, running `ffprobe` for audio/video durations, extracting audio using `ffmpeg`, and converting video frames to JPG formats.

#### [NEW] [chunking.py](file:///d:/projects/sps_project/backend/services/chunking.py)
Implements `ChunkingService` containing segmentations for:
- Text: 500 characters, 50 characters overlap.
- Audio: 30-second segments.
- Video: 2-second segments with visual frame metadata mappings.

#### [NEW] [ingestion.py](file:///d:/projects/sps_project/backend/services/ingestion.py)
Implements `IngestionService` orchestrating UploadService, MediaProcessorService, and ChunkingService, executing database entries.

---

### API Routing

#### [NEW] [upload.py (api)](file:///d:/projects/sps_project/backend/api/upload.py)
Implements `POST /api/upload` endpoint using `UploadFile` and injecting dependencies.

#### [MODIFY] [router.py](file:///d:/projects/sps_project/backend/api/router.py)
Includes the upload route under the v1 API registry.

---

### Documentation In /docs folder

All 9 requested markdown files will be written under `d:\projects\sps_project\docs/`:
1.  [architecture.md](file:///d:/projects/sps_project/docs/architecture.md) - Clean architecture system overview.
2.  [ingestion_pipeline.md](file:///d:/projects/sps_project/docs/ingestion_pipeline.md) - Visualized pipeline workflow description.
3.  [database_schema.md](file:///d:/projects/sps_project/docs/database_schema.md) - Relationship constraints of Assets and Chunks tables.
4.  [api_reference.md](file:///d:/projects/sps_project/docs/api_reference.md) - Interactive API documentation for endpoints.
5.  [media_processing.md](file:///d:/projects/sps_project/docs/media_processing.md) - Detail of ffmpeg / ffprobe subprocess executions.
6.  [chunking_strategy.md](file:///d:/projects/sps_project/docs/chunking_strategy.md) - Overlap parameters and segmentation equations.
7.  [future_ai_pipeline.md](file:///d:/projects/sps_project/docs/future_ai_pipeline.md) - Next phase plans for CLIP, Whisper, and BGE models.
8.  [deployment_guide.md](file:///d:/projects/sps_project/docs/deployment_guide.md) - Run and build instructions.
9.  [troubleshooting.md](file:///d:/projects/sps_project/docs/troubleshooting.md) - Validation errors, permissions issues, FFMpeg failures.

---

## Verification Plan

### Automated Verification
- Verify the compilation of all written service modules and API files:
  ```bash
  python -m py_compile backend/services/*.py backend/api/*.py
  ```

### Manual Verification
1. Re-build the Docker environment:
   ```bash
   docker-compose up --build -d
   ```
2. Create dummy input files for validation:
   - Text file (`dummy.txt`)
   - PDF file (`dummy.pdf`)
   - Mock audio/video files
3. Test upload pipeline via cURL requests:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/upload" -F "file=@dummy.txt"
   ```
4. Confirm response body format:
   ```json
   {
     "asset_id": "...",
     "status": "processed",
     "chunks_created": 3
   }
   ```
5. Inspect the database container tables to ensure that the asset rows are created and `asset_chunks` entries show correct chunk indices, contents, start/end timestamps, and `embedding = NULL`.
