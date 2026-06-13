# Search Analytics and Performance Tracking

This document covers the search analytics logging system, database tracking tables, and latency measurement details.

## Purpose

To track performance metrics, search trends, latency logs, and empty match distributions, enabling continuous monitoring and offline evaluations.

## Database Schema Design

Telemetry data is saved to the `search_logs` table, which is mapped via the `SearchLog` SQLAlchemy entity:

```sql
CREATE TABLE search_logs (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    latency_ms FLOAT NOT NULL,
    results_count INTEGER NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT timezone('utc'::text, now())
);
```

- **id**: Unique UUID identifier.
- **query**: Raw string query input.
- **latency_ms**: Total elapsed time from API request parsing to result output (measured in milliseconds using high-precision python counters).
- **results_count**: Count of items returned after ResultAggregator filters.
- **created_at**: High-precision UTC timestamp.

## Flow of Execution

1. `SearchService.execute_search` captures the start time using `time.perf_counter()`.
2. Following result aggregation, the latency is computed:
   `latency_ms = (time.perf_counter() - start_time) * 1000.0`
3. `SearchAnalyticsService.log_search` is called async.
4. A new `SearchLog` object is added to the active database session and committed.
5. In case of database logging failures, errors are captured and logged locally to prevent disrupting user search requests.

## Tradeoffs

- **Synchronous Telemetry Commit**: Committing analytics to PostgreSQL inside the active session introduces a minor write overhead to the search request (~2-5ms).
- **No User PII Masking**: The raw queries are stored directly. To meet privacy policies, search text might need sanitization or hashing.

## Future Improvements

- **Out-of-band Logging Queue**: Route telemetry events through Redis/Celery workers to execute database writes asynchronously, decoupling log writes from API response times.
- **Aggregated Analytics Dashboard**: Build API endpoints to query average query latencies, search volume, and popular keywords.
