# Phase 4: AI Model Integration Layer & Embedding Generation Pipeline

Design and implement a production-grade AI model integration layer and embedding generation pipeline. This will load and run sentence-transformers (BGE-M3), CLIP, and Faster-Whisper models, extract multi-modal visual and semantic text representation vectors, and bulk-update PostgreSQL asset chunk rows with 512-dimensional normalized embeddings.

## User Review Required

> [!IMPORTANT]
> To comply with the **512-dimension** database constraint, the output of BGE-M3 (1024-dimensional) is sliced to the first 512 dimensions and L2-normalized. CLIP output is naturally 512-dimensional and will be normalized as well.
>
> We initialize models via a thread-safe singleton manager (`AIModelManager`) to avoid reloading models on requests.
>
> Chunks are bulk-updated in batches of 50 to 100 using a single transaction update block.
>
> We will add the required AI libraries (`torch`, `transformers`, `sentence-transformers`, `faster-whisper`, `pillow`) to `requirements.txt`.

## Open Questions

There are no major open questions. The models, dimensions, pipelines, and bulk update rules are fully specified.

## Proposed Changes

### Dependencies & Configuration Updates

#### [MODIFY] [requirements.txt](file:///d:/projects/sps_project/backend/requirements.txt)
Append:
- `torch>=2.2.0`
- `transformers>=4.38.0`
- `sentence-transformers>=2.5.0`
- `faster-whisper>=1.0.0`
- `pillow>=10.2.0`

---

### AI Model Management & Embedding Services

#### [NEW] [ai_model_manager.py](file:///d:/projects/sps_project/backend/services/ai_model_manager.py)
Implements the `AIModelManager` class containing thread-safe singleton methods:
- `load_bge_m3()`
- `load_clip()`
- `load_whisper()`

#### [NEW] [text_embedding.py](file:///d:/projects/sps_project/backend/services/text_embedding.py)
Implements `TextEmbeddingService` containing `embed_text()` which uses BGE-M3, truncates the vector to 512-dim, and performs L2-normalization.

#### [NEW] [audio_embedding.py](file:///d:/projects/sps_project/backend/services/audio_embedding.py)
Implements `AudioEmbeddingService` utilizing Faster-Whisper to transcribe audio segments locally, returns timestamped textual blocks, and embeds them using BGE-M3.

#### [NEW] [video_embedding.py](file:///d:/projects/sps_project/backend/services/video_embedding.py)
Implements `VideoEmbeddingService` converting frames to CLIP embeddings and combining them with transcribed audio track embeddings.

#### [NEW] [embedding.py](file:///d:/projects/sps_project/backend/services/embedding.py)
Implements `EmbeddingService` acting as the main interface to generate 512-dim normalized vectors for any media chunk.

#### [NEW] [processing_orchestrator.py](file:///d:/projects/sps_project/backend/services/processing_orchestrator.py)
Implements `ProcessingOrchestrator` pulling chunks with `embedding IS NULL` for a given asset, executing the embedding service, and batch-updating the database (batch size 50-100) inside an async transaction scope.

---

### API Router & Ingestion Integration

#### [MODIFY] [upload.py (api)](file:///d:/projects/sps_project/backend/api/upload.py)
Enrich the upload response to run the `ProcessingOrchestrator` synchronously after raw ingestion, returning the fully embedded asset status.

---

## Verification Plan

### Automated Verification
- Verify compilation and import safety of all new AI services:
  ```bash
  python -m py_compile backend/services/*.py
  ```

### Manual Verification
1. Rebuild and launch the stack:
   ```bash
   docker-compose up --build -d
   ```
2. Run schema initialization:
   ```bash
   docker-compose exec backend python core/init_schema.py
   ```
3. Run test ingestion:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/upload" -F "file=@sample.txt"
   ```
4. Query Postgres to verify that chunks show correct 512-dimensional floating-point array embeddings:
   ```sql
   SELECT id, asset_id, chunk_index, start_time, end_time, array_length(embedding, 1) FROM asset_chunks;
   ```
