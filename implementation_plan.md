# Phase 2: Database Design, Vector Architecture, and Schema Implementation

Design and implement a robust, production-grade database layer supporting multi-modal assets, chunk-level semantic data, pgvector integration with 512-dimension vector embeddings, HNSW index optimization for cosine similarity search, and temporal query features.

## User Review Required

> [!IMPORTANT]
> The `embedding` dimension is strictly set to **512**.
> We configure an **HNSW** index using the pgvector `vector_cosine_ops` operator class to optimize similarity queries.
> We establish the repository layer and `DatabaseService` layer to enforce transaction safety and session isolation.
> We will create a local Python database schema initialization script (`backend/core/init_schema.py`) to easily setup the database tables and trigger HNSW indexes.

## Open Questions

There are no major open questions at this point. The requirements for tables, dimensions, indexing, and repositories are fully defined.

## Proposed Changes

### Database Models

#### [NEW] [asset.py](file:///d:/projects/sps_project/backend/models/asset.py)
SQLAlchemy model mapping the `assets` table. It includes basic fields (`id`, `filename`, `file_path`, `modality` as ENUM, `created_at`, `updated_at`) and sets up relationships.

#### [NEW] [chunk.py](file:///d:/projects/sps_project/backend/models/chunk.py)
SQLAlchemy model mapping the `asset_chunks` table. It includes structural fields, temporal timestamps (`start_time`, `end_time`), a `metadata` JSONB field, and a 512-dimensional pgvector column. Sets up the HNSW index using `vector_cosine_ops` for cosine similarity queries.

#### [NEW] [__init__.py (models)](file:///d:/projects/sps_project/backend/models/__init__.py)
Exposes the database models for cleaner imports.

---

### Repository Layer

#### [NEW] [asset.py (repositories)](file:///d:/projects/sps_project/backend/repositories/asset.py)
Implements `AssetRepository` containing:
- `create_asset()`
- `get_asset_by_id()`
- `list_assets()`

#### [NEW] [chunk.py (repositories)](file:///d:/projects/sps_project/backend/repositories/chunk.py)
Implements `ChunkRepository` containing:
- `insert_chunks_bulk()`
- `search_similar_chunks()` using the `<=>` cosine distance operator and joining with the `assets` table.
- `get_chunks_by_asset()`

---

### Service Layer

#### [NEW] [database.py (services)](file:///d:/projects/sps_project/backend/services/database.py)
Implements `DatabaseService` which acts as a transaction wrapper executing business-agnostic database actions inside async transaction scopes.

---

### Database Initialization Script

#### [NEW] [init_schema.py](file:///d:/projects/sps_project/backend/core/init_schema.py)
Provides a runnable database initialization script that creates the `vector` extension and synchronizes SQLAlchemy metadata schemas with Postgres.

---

## Verification Plan

### Automated Verification
- Verify the compilation and import safety of all written models, repositories, and services using:
  ```bash
  python -m py_compile backend/models/*.py backend/repositories/*.py backend/services/*.py
  ```

### Manual Verification
1. Prepare a schema creation command:
   ```bash
   python backend/core/init_schema.py
   ```
2. Run a verification test script (`backend/scratch/verify_phase2.py` in the scratch area) that:
   - Connects to Postgres.
   - Inserts a sample `video` asset.
   - Inserts three mock chunks with 512-dimensional floating-point array embeddings.
   - Performs a vector similarity query and confirms it returns the joined record containing the asset and chunk content.
   - Outputs the similarity score.
