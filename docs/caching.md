# Caching Specification

This guide details the Redis caching design, key formats, and cache invalidation policies implemented in OmniSeek.

---

## 1. Cache Service Design

Caching is managed by `CacheService` (`services/cache.py`), which abstracts asynchronous Redis operations:

*   **Technology**: Redis-backed cache layer.
*   **Default Time-To-Live (TTL)**: `300 seconds` (5 minutes) for search results, customizable via settings.
*   **Serialization**: Data payloads are serialized to JSON strings prior to storage and parsed back into dictionaries on hits.

---

## 2. Key Schemas

To prevent namespace collisions, keys use a structured prefix naming scheme:

*   **Search Queries**:
    ```
    search:{query}:{modality}:{mode}:{limit}:{minimum_score}
    ```
    Uniquely identifies search results based on input parameters.
*   **Analytics Summaries**:
    ```
    analytics:dashboard
    ```
    Caches dashboard metric aggregations.

---

## 3. Invalidation Policy

To prevent stale search results, the system enforces a strict invalidation policy:

*   **Ingestion Uploads**: Uploading a new asset invalidates the search cache:
    ```python
    await CacheService.invalidate_pattern("search:*")
    ```
    This removes all search cache keys, ensuring new files are instantly retrievable.
*   **Manual Trigger**: Re-running database benchmarks invalidates the dashboard analytics cache to recalculate metrics.
