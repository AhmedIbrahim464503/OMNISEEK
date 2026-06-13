# Phase 5: Semantic Search Engine, Cross-Modal Retrieval, and Search API

Design and implement a production-grade semantic search engine supporting cross-modal retrieval, temporal search, result aggregation/deduplication, search analytics persistence, and query filtering.

## User Review Required

> [!IMPORTANT]
> We will add the `search_logs` table to store query analytics (including text, latency in ms, result count, and timestamps). We will update `init_schema.py` to synchronize this new table.
>
> High-dimensional indexing queries are executed asynchronously using pgvector's `<=>` cosine distance operator and joined with assets.
>
> Result aggregation merges adjacent temporal segments from the same media asset (adjacent `chunk_index` values) into a single unified result. Deduplication keeps the match with the highest similarity score.
>
> Score normalization translates raw cosine distance values safely into a human-friendly `0.0` to `1.0` range.

## Open Questions

None. The search endpoints, latency targets, and aggregation specifications are fully detailed.

## Proposed Changes

### Database Updates

#### [NEW] [search_log.py](file:///d:/projects/sps_project/backend/models/search_log.py)
SQLAlchemy model mapping the `search_logs` table. Fields: `id`, `query`, `latency_ms`, `results_count`, `created_at`.

#### [MODIFY] [__init__.py (models)](file:///d:/projects/sps_project/backend/models/__init__.py)
Exposes the new `SearchLog` model.

#### [MODIFY] [init_schema.py](file:///d:/projects/sps_project/backend/core/init_schema.py)
Includes imports for the `SearchLog` model to sync schemas on startup.

---

### Repository Layer

#### [NEW] [search.py (repositories)](file:///d:/projects/sps_project/backend/repositories/search.py)
Implements `SemanticSearchRepository` carrying out async similarity queries, joining chunks with assets, and filtering by modality.

---

### Service Layer

#### [NEW] [search_embedding.py](file:///d:/projects/sps_project/backend/services/search_embedding.py)
Implements `SearchEmbeddingService` using the cached BGE-M3 model to embed natural language query strings, slicing vectors to 512 dimensions, and normalizing results.

#### [NEW] [search_analytics.py](file:///d:/projects/sps_project/backend/services/search_analytics.py)
Implements `SearchAnalyticsService` writing search queries, elapsed milliseconds, and result counts to the `search_logs` table.

#### [NEW] [search.py (services)](file:///d:/projects/sps_project/backend/services/search.py)
Implements the core `SearchService` orchestrating embedding, candidate retrieval, score normalization, result aggregation (merging adjacent segments), duplicate filtering, and analytics logging.

---

### API Routing

#### [NEW] [search.py (api)](file:///d:/projects/sps_project/backend/api/search.py)
Implements `GET /api/search` with parameters `q` (query text) and `modality` (optional filter).

#### [MODIFY] [router.py](file:///d:/projects/sps_project/backend/api/router.py)
Includes the search route under the `/api` and `/api/v1` routers.

---

### System Documentation Updates (In /docs folder)

We will write the following 6 markdown files under `docs/`:
1.  [semantic_search.md](file:///d:/projects/sps_project/docs/semantic_search.md) - Conceptual details of text semantic matching.
2.  [vector_retrieval.md](file:///d:/projects/sps_project/docs/vector_retrieval.md) - Details of pgvector HNSW query structures and distances.
3.  [cross_modal_search.md](file:///d:/projects/sps_project/docs/cross_modal_search.md) - How CLIP and BGE models are queried together.
4.  [search_api.md](file:///d:/projects/sps_project/docs/search_api.md) - GET /search parameter filters and schema guides.
5.  [result_aggregation.md](file:///d:/projects/sps_project/docs/result_aggregation.md) - Merging rules for adjacent chunks and filters.
6.  [search_analytics.md](file:///d:/projects/sps_project/docs/search_analytics.md) - Relational DB tracking logs for metrics.

And modify:
*   [architecture.md](file:///d:/projects/sps_project/docs/architecture.md) - Expand with search service layers and log models.

---

## Verification Plan

### Automated Verification
- Compile code to verify import safety and typing consistency:
  ```bash
  python -m py_compile backend/models/*.py backend/repositories/*.py backend/services/*.py backend/api/*.py
  ```

### Manual Verification
1. Run schema migrations/init:
   ```bash
   docker-compose exec backend python core/init_schema.py
   ```
2. Test upload of a document to create chunk records.
3. Trigger search query using cURL requests:
   ```bash
   curl "http://localhost:8000/api/search?q=AI+vectors"
   ```
4. Confirm response contains aggregated matching chunks with timestamps and normalized similarity scores.
5. Inspect the `search_logs` table to confirm that query texts, latencies (in milliseconds), and result counts were tracked correctly.
