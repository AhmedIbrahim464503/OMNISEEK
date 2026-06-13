# Future AI Embedding Pipeline Specifications

This document outlines the design intent and models planned for Phase 4 to construct high-dimensional vector representations.

---

## 1. Targeted AI Models

*   **Text Embedding**: `BAAI/bge-m3` mapping natural language text chunks to a dense 512-dimensional vector.
*   **Visual Frame Embedding**: `CLIP ViT-B/32` mapping video JPG frames to matching dense 512-dimensional visual vector slots.
*   **Audio Transcription**: `Faster-Whisper` (local inference engine) transcribing 30-second audio files into timestamped text strings, which are then passed to `BAAI/bge-m3` to yield text embeddings.

---

## 2. Dynamic Integration Workflow

```
[Ingested Asset Chunks (embedding=NULL)]
                 │
                 ▼
     [Select Processing Route]
      ├── TEXT  ──► BGE-M3 (Text Embedder) ────────────────────┐
      ├── AUDIO ──► Whisper Transcriber ──► BGE-M3 ────────────┼──► [Update DB: 512-dim Vector]
      └── VIDEO ──► Frame Demuxer ──► CLIP (Visual Embedder) ──┘
```

During Phase 4, the database service will retrieve all chunks with `embedding IS NULL`, process them in batches through memory-cached singleton model instances, and update `asset_chunks.embedding` using transaction-safe SQL calls.
