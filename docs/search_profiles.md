# Configurable Search Profiles

This document maps the Fast, Balanced, and Accurate search profiles to their corresponding execution modes, latency parameters, and use cases.

## Purpose

Different search use cases require different tradeoffs between response speed and search precision. Exposing configurable profiles lets users query the same endpoint with varying parameters depending on their hardware and accuracy constraints.

## Profile Configurations

| Profile Mode | Strategy Name | Sub-component Execution Steps | Target Latency | Ideal Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Fast** | Fast (Vector Only) | 1. BGE-M3 Query Embedding<br>2. Vector Index Retrieval<br>3. Score Normalization | < 300ms | Real-time autocomplete, suggestions, low-spec CPU hosting. |
| **Balanced** | Balanced (Hybrid) | 1. Query Embedding<br>2. Vector Search + Postgres FTS<br>3. Weighted Score Fusion | < 700ms | Standard query execution, keyword-heavy user queries. |
| **Accurate** | Accurate (Hybrid + Reranked) | 1. Query Embedding<br>2. Vector + FTS Search (Top 50)<br>3. Hybrid Fusion<br>4. Cross-Encoder Reranking | < 1500ms | Detailed search investigations, where finding all relevant results is critical. |

## Profile Parameter Control

API requests control the profile via the `mode` parameter:
```http
GET /api/search?q=neural+networks&mode=accurate&top_k=10&minimum_score=0.40
```
- **mode**: `fast`, `balanced`, or `accurate` (default: `fast`).
- **top_k**: Slices the final results pool (default: `20`).
- **minimum_score**: Discards noisy results scoring below this score threshold (default: `0.30`).

## Tradeoffs

- **Accurate Profile Overhead**: Accurate Mode runs Cross-Encoder scoring which consumes more CPU cycles. This mode is restricted to the top 50 candidates to maintain response times under 1.5 seconds on standard CPU hardware.

## Future Improvements

- **Adaptive Profiles**: Automatically degrade from Accurate to Balanced mode if system load or concurrent request volumes exceed predefined thresholds.
