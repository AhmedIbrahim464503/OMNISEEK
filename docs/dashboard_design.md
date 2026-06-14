# Dashboard Design

This guide details the layout, data synchronization, and components of the OmniSeek Systems Dashboard.

---

## 1. Grid Metrics & Telemetry KPIs

The primary dashboard layout uses a responsive 4-column grid displaying key ingestion and search metrics:

*   **Total Uploaded Assets**: Count of files processed.
*   **Total Vector Chunks**: Sum of vector partitions across all file modalities.
*   **Total Engine Queries**: Cumulative search query executions.
*   **Average Latency**: End-to-end response speeds (formatted dynamically as `ms` or `s`).

---

## 2. Ingest Queue & Activity Logs

Below the primary metrics card block, a split layout renders recent activities:

### Ingestion Queue (Left Panel):
*   Tracks the 10 most recent uploads.
*   Pulls filenames, upload times, and statuses (Processing, Completed, Failed).
*   Updates status badges (Amber pulsating indicator for processing, green for indexed, red for failed uploads).

### Recent User Queries (Right Panel):
*   Logs search terms, execution modes, hit counts, and query times.
*   Retrieves values directly from the persistent Zustand storage store.
*   Provides quick navigation links to the main search console.
