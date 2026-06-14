# Analytics telemetry Dashboard

This document details the telemetry metrics, performance charts, and analytical graphs in the OmniSeek dashboard.

---

## 1. Metrics & Charts Layout

The Analytics dashboard renders real-time performance telemetry collected from database logs:

### A. Sub-Component Latency Breakdown
*   **Visualizer**: Recharts stacked `BarChart`.
*   **Data Points**: Compares query profiles (Fast vs Balanced vs Accurate).
*   **Slices**: Divides retrieval times (database semantic/lexical operations) from reranker times (CPU cross-encoder execution).

### B. Modality Index Distribution
*   **Visualizer**: Recharts donut `PieChart`.
*   **Slices**: Visualizes percentages of chunks indexed across Text, Audio, and Video files.

### C. Search Retrieval Accuracy
*   **Details**: Summarizes precision metrics (NDCG, MRR, Precision, Recall).
*   **Methodology**: Calculated via testing scripts against ground truth evaluation suites.

---

## 2. Dynamic Top Queries

*   Tracks search frequency lists logged inside `search_performance_logs`.
*   Displays search terms and execution counts in descending order.
*   Enables search developers to analyze query popularity and performance patterns.
