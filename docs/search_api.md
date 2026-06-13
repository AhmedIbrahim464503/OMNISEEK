# Search API Endpoint

This document outlines the API specification, query parameters, filters, and response schemas for the semantic search endpoint.

## Purpose

Provides a standard REST interface for performing semantic multi-modal search across all processed assets in the OMNISEEK system.

## API Endpoint Specification

### `GET /api/search` (and `GET /api/v1/search`)

Retrieves a ranked list of media segments matching the input query string.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `q` | `string` | Yes | - | Natural language search query. Cannot be empty or whitespace. |
| `modality` | `string` | No | - | Optional filter to restrict results to a single modality: `TEXT`, `AUDIO`, or `VIDEO`. |
| `limit` | `integer`| No | `20` | Maximum number of candidate chunks to retrieve initially from the database. |
| `threshold`| `float` | No | `0.0` | Minimum quality threshold (normalized score `0.0` to `1.0`). |

#### Response Schema (JSON)

```json
{
  "query": "machine learning",
  "count": 1,
  "results": [
    {
      "asset_id": "87e3fd2b-7765-45d9-ad40-ecc000fcd128",
      "asset_name": "lecture_01.mp4",
      "modality": "VIDEO",
      "content": "In this slide, we introduce neural network weights optimization techniques.",
      "start_time": 120.0,
      "end_time": 150.0,
      "score": 0.9412
    }
  ]
}
```

## Flow of Execution

1. FastAPI route handler validates parameters. If `q` is empty, raises `HTTPException 400`.
2. Database dependency yields an `AsyncSession` injected into `SearchService`.
3. `SearchService.execute_search` runs query embedding, candidates retrieval, score normalization, result aggregation/filtering, and logs execution details.
4. Response is serialized and returned to client.

## Tradeoffs

- **Synchronous API with Async Database**: The API is written using standard FastAPI async route handlers, which scale extremely well under high load. However, AI model inference is currently executed synchronously on CPU threads, blocking the event loop briefly. This is mitigated by run-time caching and locking.

## Future Improvements

- **Pagination Support**: Add cursor-based or offset-based pagination.
- **Async Embedding Queue**: Run query embeddings inside a thread pool or route to dedicated GPU inference workers to avoid blocking the event loop.
