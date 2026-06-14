# Metrics Monitoring (Prometheus & Grafana)

This guide documents the Prometheus metrics integration, scrape formats, and Grafana dashboard setups.

---

## 1. Prometheus Telemetry Exporter

FastAPI exposes metrics at the `/metrics` endpoint in standard Prometheus plain-text format:

### Active Scrape Keys:
*   `http_requests_total{method, path, status}`: Cumulative request counter.
*   `http_request_duration_seconds_avg{method, path}`: Average request latency.
*   `celery_tasks_total{name, status}`: Background queue task tracker.
*   `db_query_duration_seconds_avg`: Database transaction latency.
*   `search_latency_seconds_avg{mode}`: Multi-modal search latency.

---

## 2. Grafana Dashboards

Grafana dashboards are configured in JSON templates under `grafana/dashboards/`:

### A. API Monitoring (`api_monitoring.json`)
*   **Visualizations**: Timeseries graphs for request volume (queries/sec) and latency trends.

### B. Search Performance (`search_monitoring.json`)
*   **Visualizations**: Timeseries graphs comparing search modes (Fast vs Balanced vs Accurate) and total search queries.

### C. Background Workers (`worker_monitoring.json`)
*   **Visualizations**: Task throughput rate and status counters (success vs failure vs retries).

### D. Database Health (`database_monitoring.json`)
*   **Visualizations**: Database transaction latencies to detect slow queries.

### E. System Health (`system_health.json`)
*   **Visualizations**: HTTP error counts (4xx/5xx responses) and system success rates.
