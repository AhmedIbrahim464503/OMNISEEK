# Phase 5 Walkthrough: Semantic Search Engine, Cross-Modal Retrieval, and Search API

This document details the components, logic flows, schema setups, and execution verification for the semantic cross-modal retrieval system implemented in Phase 5.

---

## 1. Updated Folder Structure

The backend workspace is structured as follows:

```
OMNISEEK/
├── backend/
│   ├── api/
│   │   ├── router.py         <-- [MODIFY] Registered search API endpoints
│   │   ├── search.py         <-- [NEW] GET /api/search API route handler
│   │   └── upload.py
│   ├── core/
│   │   ├── celery.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── exceptions.py
│   │   ├── init_schema.py    <-- [MODIFY] Added SearchLog import to auto-migrate table
│   │   └── logging.py
│   ├── models/
│   │   ├── __init__.py       <-- [MODIFY] Expose SearchLog
│   │   ├── asset.py
│   │   ├── base.py
│   │   ├── chunk.py          <-- [MODIFY] Solved metadata name collision with fallback getters/setters
│   │   └── search_log.py     <-- [NEW] Search analytics db schema mapping
│   ├── repositories/
│   │   ├── asset.py
│   │   ├── base.py
│   │   ├── chunk.py
│   │   └── search.py         <-- [NEW] SemanticSearchRepository for pgvector matching
│   ├── services/
│   │   ├── ai_model_manager.py
│   │   ├── audio_embedding.py
│   │   ├── base.py
│   │   ├── chunking.py
│   │   ├── database.py
│   │   ├── embedding.py
│   │   ├── ingestion.py
│   │   ├── media_processor.py
│   │   ├── processing_orchestrator.py
│   │   ├── search.py         <-- [NEW] SearchService orchestrator with ResultAggregator, DuplicateResultFilter, and ScoreNormalizer
│   │   ├── search_analytics.py <-- [NEW] Persists metrics telemetry into search_logs
│   │   ├── search_embedding.py <-- [NEW] BGE-M3 text query generator (512-dim normalized slice)
│   │   ├── text_embedding.py
│   │   ├── upload.py
│   │   └── video_embedding.py
│   ├── tests/
│   │   └── test_search.py    <-- [NEW] Unit/Integration test suites (FastAPI client, mock loaders)
│   ├── main.py
│   └── requirements.txt
├── docs/                     <-- [NEW] Created 6 reference guides and updated system architecture
│   ├── api_reference.md
│   ├── architecture.md
│   ├── chunking_strategy.md
│   ├── cross_modal_search.md
│   ├── database_schema.md
│   ├── deployment_guide.md
│   ├── future_ai_pipeline.md
│   ├── ingestion_pipeline.md
│   ├── media_processing.md
│   ├── result_aggregation.md
│   ├── search_analytics.md
│   ├── search_api.md
│   ├── semantic_search.md
│   ├── troubleshooting.md
│   └── vector_retrieval.md
├── docker-compose.yml
├── development_history.md
├── agent_behavior_guidelines.md
├── implementation_plan.md
└── task.md
```

---

## 2. Key Code Implementations

### A. Repository Layer: [search.py](file:///d:/projects/sps_project/backend/repositories/search.py)
Uses pgvector's `<=>` (cosine distance) operator to query database chunks matching the query vector, joining with assets and supporting modality filters:
```python
distance = AssetChunk.embedding.cosine_distance(query_vector)
stmt = select(...).join(Asset).order_by(distance.asc()).limit(limit)
```

### B. Core Search Orchestration: [search.py](file:///d:/projects/sps_project/backend/services/search.py)
Coordinated by `SearchService`, it utilizes:
1. **`ScoreNormalizer`**: Translates raw distance scores to a human-friendly range `[0.0, 1.0]`.
2. **`DuplicateResultFilter`**: Removes duplicate matches keeping the highest score.
3. **`ResultAggregator`**: Merges adjacent sequential chunk indices from the same asset into single temporal segments.
4. **`SearchAnalyticsService`**: Writes search queries, latencies, and result counts to the `search_logs` table.

### C. Search API Router: [search.py](file:///d:/projects/sps_project/backend/api/search.py)
FastAPI routes mapping `GET /api/search` with validation and error handling:
```python
@router.get("/search")
async def search(q: str, modality: Optional[str] = None, threshold: float = 0.0, db: AsyncSession = Depends(get_db)):
    ...
```

---

## 3. Testing and Verification

A comprehensive test suite covering all 7 test areas is defined in `backend/tests/test_search.py`.

### Test Executions
Run the tests using standard python unittest:
```bash
python -m unittest backend/tests/test_search.py
```

Output:
```
Ran 11 tests in 0.473s
OK
```

---

## 4. Setup and Run Guide

1. Re-synchronize schemas to generate the `search_logs` table:
   ```bash
   docker-compose exec backend python core/init_schema.py
   ```
2. Search through the browser/cURL interface:
   ```bash
   curl "http://localhost:8000/api/search?q=machine+learning"
   ```
   Or restrict to a specific modality:
   ```bash
   curl "http://localhost:8000/api/search?q=milk&modality=VIDEO"
   ```
