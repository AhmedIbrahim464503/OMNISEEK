# Phase 6: Advanced Retrieval Intelligence & Evaluation Framework

Upgrade the basic semantic search engine to an enterprise-grade retrieval system utilizing cross-encoder reranking, full-text hybrid search, explainable matches, latency monitoring, search quality metrics, and performance benchmarking.

---

## User Review Required

> [!IMPORTANT]
> - We will run cross-encoder reranking locally inside the container using the BAAI model `BAAI/bge-reranker-base` (270M parameters) or `BAAI/bge-reranker-large` (335M parameters) for CPU. `bge-reranker-base` is highly recommended for balanced CPU performance and accuracy.
> - We will add two new database tables: `evaluation_runs` and `search_performance_logs`. We will update `init_schema.py` to synchronize these tables.
> - PostgreSQL Full Text Search (`ts_vector` and `ts_rank`) will be used for the keyword search component of Hybrid Search.
> - We will support configurable weight weights for Hybrid fusion.

---

## Open Questions

None.

---

## Proposed Changes

### 1. Model Layer & Database Updates

#### [NEW] [evaluation_run.py](file:///d:/projects/sps_project/backend/models/evaluation_run.py)
SQLAlchemy model mapping the `evaluation_runs` table. Fields: `id`, `query`, `metric_name`, `metric_value`, `created_at`.

#### [NEW] [performance_log.py](file:///d:/projects/sps_project/backend/models/performance_log.py)
SQLAlchemy model mapping the `search_performance_logs` table. Fields: `id`, `query`, `retrieval_ms`, `rerank_ms`, `total_ms`, `created_at`.

#### [MODIFY] [__init__.py (models)](file:///d:/projects/sps_project/backend/models/__init__.py)
Imports and exposes `EvaluationRun` and `SearchPerformanceLog`.

#### [MODIFY] [init_schema.py](file:///d:/projects/sps_project/backend/core/init_schema.py)
Includes imports for the new models to synchronize database tables.

---

### 2. Repository Layer

#### [MODIFY] [search.py (repositories)](file:///d:/projects/sps_project/backend/repositories/search.py)
Add keyword-based Full-Text Search matching on `AssetChunk.content` using `ts_rank` to enable hybrid score fusion.

---

### 3. Service Layer

#### [MODIFY] [ai_model_manager.py](file:///d:/projects/sps_project/backend/services/ai_model_manager.py)
Extend the singleton model manager to load the `BAAI/bge-reranker-base` Cross-Encoder model thread-safely on CPU.

#### [NEW] [reranker.py](file:///d:/projects/sps_project/backend/services/reranker.py)
Implements `RerankerService` to compute cross-encoder similarity scores between query-document pairs in batches.

#### [NEW] [hybrid_search.py](file:///d:/projects/sps_project/backend/services/hybrid_search.py)
Implements `HybridSearchService` running both semantic vector search and database full-text search, and combining scores using weighted fusion.

#### [NEW] [explainability.py](file:///d:/projects/sps_project/backend/services/explainability.py)
Implements `ExplainabilityService` generating descriptive match reasons and listing semantic, keyword, and fused scores.

#### [NEW] [evaluation.py](file:///d:/projects/sps_project/backend/services/evaluation.py)
Implements `EvaluationService` computing NDCG, Mean Reciprocal Rank (MRR), Precision@K, Recall@K, and Accuracy@K, and logging results to `evaluation_runs`.

#### [NEW] [benchmark.py](file:///d:/projects/sps_project/backend/services/benchmark.py)
Implements `SearchBenchmarkService` running benchmark queries against Vector, Hybrid, and Reranked search pipelines, generating a tabular comparative performance report.

#### [NEW] [quality_filter.py](file:///d:/projects/sps_project/backend/services/quality_filter.py)
Implements `ResultQualityFilter` to discard noisy results beneath a threshold and identify/suppress near-duplicate segments.

#### [MODIFY] [search.py (services)](file:///d:/projects/sps_project/backend/services/search.py)
Update `SearchService` to orchestrate execution profiles:
*   **Fast**: Vector search only.
*   **Balanced**: Full hybrid search (vector + text).
*   **Accurate**: Hybrid search + Cross-Encoder reranking.
Also measures sub-component latency breakdown and persists log entries.

---

### 4. API Routing

#### [MODIFY] [search.py (api)](file:///d:/projects/sps_project/backend/api/search.py)
Exposes endpoint updates:
*   `GET /api/search`: Supports parameters `mode` (`fast`, `balanced`, `accurate`), `top_k`, and `minimum_score`. Response payload returns latency breakdowns, search strategy, and explanation dictionaries.
*   `GET /api/search/dashboard`: Exposes backend statistics: average latency, precision, recall, top queries, and performance breakdowns.
*   `POST /api/search/benchmark`: Triggers search benchmark runs and returns comparative evaluations.

---

### 5. Documentation Updates

We will add the following 7 markdown guides under `docs/`:
1.  [reranking.md](file:///d:/projects/sps_project/docs/reranking.md) - Details on Cross-Encoder scoring and batches.
2.  [hybrid_search.md](file:///d:/projects/sps_project/docs/hybrid_search.md) - Information on Full-Text Search and fusion parameters.
3.  [explainability.md](file:///d:/projects/sps_project/docs/explainability.md) - Rationale and metadata formatting guides.
4.  [search_metrics.md](file:///d:/projects/sps_project/docs/search_metrics.md) - Formula explanations for MRR, NDCG, and Recall.
5.  [search_benchmarking.md](file:///d:/projects/sps_project/docs/search_benchmarking.md) - Execution parameters for comparison benchmarking.
6.  [search_profiles.md](file:///d:/projects/sps_project/docs/search_profiles.md) - Mapping of profiles (Fast, Balanced, Accurate) to service execution steps.
7.  [performance_monitoring.md](file:///d:/projects/sps_project/docs/performance_monitoring.md) - Telemetry collection schema details.

And update:
*   [architecture.md](file:///d:/projects/sps_project/docs/architecture.md) - Reflect Phase 6 services.

---

## Verification Plan

### Automated Verification
Run unit tests verifying the reranking model mock, hybrid search fusion, metric calculations, and api endpoints:
```bash
docker compose exec backend python -m unittest tests/test_search.py
```

### Manual Verification
1. Re-build backend and sync the new database models:
   ```bash
   docker compose up -d --build
   docker compose exec backend python -m core.init_schema
   ```
2. Trigger the benchmark suite to verify comparative metric reports:
   ```bash
   curl -X POST "http://localhost:8000/api/search/benchmark"
   ```
3. Inspect database tables `evaluation_runs` and `search_performance_logs` to ensure metrics and latencies are saved correctly.
