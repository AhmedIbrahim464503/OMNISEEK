# OMNISEEK Agent Behavior & Coding Guidelines

This document serves as the absolute reference for code style, architectural constraints, and behavior rules followed during the construction of the OMNISEEK system. Any human or AI developer modifying this codebase should strictly adhere to these rules.

---

## 1. Programming Language & Formatting Rules
*   **Python Version**: Python 3.11+
*   **Asynchronous Contexts**: FastAPI route handlers, database connections, sessions, and database queries must run asynchronously (`async/await`).
*   **Validation**: Pydantic v2 must be used for input validation, query parameters, and serializations.
*   **Type Hints**: Strict type hinting must be implemented on all variables, functions, and class signatures.
*   **No Placeholders**: Avoid utilizing `pass` or `TODO` annotations. Placeholders should be replaced with descriptive docstrings or base implementations.
*   **Structured Logging**: Never use `print()` statements for diagnostic logging. Always utilize the structured JSON logger defined in `backend/core/logging.py`.

---

## 2. Architectural Layer Constraints
The codebase strictly follows a clean architecture pattern divided into five primary directories under `backend/`:

1.  **api/**: FastAPI routes, path endpoints, request routers, and dependencies injection.
2.  **core/**: Central configuration parsing settings from `.env`, structured logger setups, SQLAlchemy database engine session generators, and custom exception types.
3.  **models/**: Declarative database model representations mapping Postgres tables.
4.  **schemas/**: Pydantic schemas validating input payloads and formats.
5.  **repositories/**: Independent database communication layer encapsulating SQL query constraints. No business validations or transaction controllers should sit here.
6.  **services/**: Business logic layer coordinating workflows. Wraps database repository mutations inside database transaction boundaries (commit, rollback).
7.  **workers/**: Background tasks worker configurations managed via Celery and Redis.

---

## 3. Database & pgvector Constraints
*   **Engine**: Postgres 15+ running the `pgvector` extension.
*   **Lifespan Initialization**: Database extensions must be initialized programmatically during system startup using:
    ```sql
    CREATE EXTENSION IF NOT EXISTS vector;
    ```
*   **Dimension**: High-dimensional vector embeddings are strictly configured to **512 dimensions**.
*   **Distance Metric**: Cosine similarity is the mandatory metric used for vector matchings.
*   **Vector Indexing**: Use HNSW indexing on the `embedding` column matching the `vector_cosine_ops` operator class to optimize similarity performance:
    ```sql
    CREATE INDEX ON asset_chunks USING hnsw (embedding vector_cosine_ops);
    ```

---

## 4. Environment Variables
*   Centralize variables using `pydantic-settings` within `backend/core/config.py`.
*   Maintain `.env.example` as a template for variables required by database, redis, and uvicorn container stacks.
*   Exclude personal `.env` files from Git by using the `.gitignore` exclusion directives.
