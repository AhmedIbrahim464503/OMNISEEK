# Evaluator Demo Guide

This guide provides a step-by-step walkthrough script for evaluating the OmniSeek system.

---

## 1. System Set Up

Verify the containers are running and database schemas are synced:
```bash
docker compose up -d
docker exec omniseek-backend python -m core.init_schema
```

---

## 2. Ingestion Upload Demo

1.  Open [http://localhost:3000](http://localhost:3000) and navigate to the **Upload Center**.
2.  Drag and drop a test file (such as a text document, audio track, or video clip).
3.  **Observation**: The upload progress bar updates, the file status transitions from Pending to Ingesting, and the backend offloads processing to the Celery worker task `process_asset_embeddings`.
4.  Verify status transitions in the **Ingestion Queue** on the dashboard.

---

## 3. Multi-Modal Search Demo

1.  Navigate to the **Search Center**.
2.  Select **Settings** (gear icon) to toggle parameters:
    *   Set mode to **Accurate** (enables hybrid search with cross-encoder reranking).
    *   Set **Minimum confidence score** to `30%`.
3.  Input a query (e.g. `"coding pipelines"` or `"milk"`).
4.  **Observation**: The results show modality icons, confidence percentages, latency metrics, and explainability summaries.
5.  Select **Explain Match** to view the score breakdown:
    *   Semantic Similarity
    *   Lexical FTS Rank
    *   Cross-Encoder Rerank

---

## 4. Temporal Retrieval Playback Demo

1.  Select **Launch Media** on a search result:
    *   *Video*: Opens the HTML5 player and seeks to the matched timestamp.
    *   *Audio*: Opens the audio player and seeks to the matched timestamp.
    *   *Text*: Opens the document viewer and highlights the matched text snippet.
