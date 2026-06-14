# Final System Architecture

This guide details the final production system architecture, security controls, and observability middleware layers implemented in OmniSeek.

---

## 1. System Topology

The final production topology isolates security and processing boundaries:

```mermaid
graph TD
    Client[Browser Frontend: Next.js] --> Security[Security Middleware: CSP/HSTS/Auth]
    Security --> Router[FastAPI API Router]
    Router --> RateLimit{Rate Limiter: Redis}
    RateLimit -->|Pass| Services[Service Layer: Search/Ingestion/Auth]
    Services --> DB[(PostgreSQL + pgvector)]
    Services --> Cache[(Redis Cache Layer)]
    Services --> Queue[Celery Queue: Task statuses]
```

---

## 2. Decoupled Service Organization

The backend is built using a clean, decoupled architecture:

*   **API Layer** (`backend/api/`): Exposes REST endpoints, validates inputs, and enforces authorization and rate limits.
*   **Service Layer** (`backend/services/`): Orchestrates business logic, manages cache entries, and coordinates db transaction contexts.
*   **Model Layer** (`backend/models/`): Maps SQLAlchemy entities. Added `User` and `TaskStatus` to support security and tracking.
*   **Repository Layer** (`backend/repositories/`): Handles SQL queries, vector cosine similarities, and PostgreSQL Full-Text Search.
*   **Infrastructure Configuration** (`backend/core/`): Centralizes settings validation, logging configurations, and database connection pools.
