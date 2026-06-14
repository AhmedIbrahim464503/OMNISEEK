# Observability & Structured Logs

This guide details the logging formats, telemetry metrics, and tracing variables implemented in the OmniSeek backend.

---

## 1. Tracing Context & Trace IDs

To track query flows across clean layers, every HTTP request registers a unique request ID and trace ID:

*   **Generation**: The tracing middleware parses incoming headers (`X-Request-ID` / `X-Trace-ID`) or generates new UUIDs if absent.
*   **Trace Context**: Binds identifiers to a thread-safe `request_context` ContextVar:
    ```python
    request_context.set({"request_id": request_id, "trace_id": trace_id})
    ```
*   **Response Headers**: Returns `X-Request-ID` and `X-Trace-ID` headers to the client.

---

## 2. Structured JSON Logging

Logs are formatted in structured JSON format via `JSONFormatter` in `core/logging.py`, making them directly compatible with tools like ElasticSearch, Loki, or Datadog.

### Log Schema:
```json
{
  "timestamp": "2026-06-14 08:52:43,456",
  "level": "INFO",
  "name": "omniseek",
  "message": "API search request received from User [john_doe]: q='vector database'",
  "filename": "search.py",
  "lineno": 29,
  "request_id": "0d632fe0-658b-4a5f-9db0-128a8d11c0f0",
  "trace_id": "9d90adcf-77df-44cf-a39d-de6cfa2b2026"
}
```

---

## 3. Telemetry Metrics Collected

The system collects granular performance telemetry, recorded thread-safely in `MetricsCollector`:

*   **API Execution Latency**: Request durations grouped by method, path, and response status.
*   **Search Latency**: Times recorded by profile mode (Fast, Balanced, Accurate).
*   **Database Query Time**: Duration of database transactions.
*   **Background Tasks**: Execution times for Celery background tasks.
*   **Embedding Pipeline Time**: Generation times for CLIP, Whisper, and BGE models.
