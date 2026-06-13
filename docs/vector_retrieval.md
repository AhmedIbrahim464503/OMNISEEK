# Vector Retrieval Layer

This document describes the vector retrieval layer, pgvector operations, indexing strategies, and database query parameters.

## Purpose

The Vector Retrieval Layer performs fast vector similarity matching against database records using PostgreSQL's pgvector extension. It retrieves database rows representing asset chunks based on their proximity to a query embedding.

## Design

### 1. Vector Distance Metric
We use **Cosine Distance** (denoted by the `<=>` operator in pgvector) to compare vectors:
$$CosineDistance(u, v) = 1 - \frac{u \cdot v}{\|u\| \|v\|}$$
Because all database and query vectors are L2-normalized upon creation, the magnitude of the vectors is exactly `1.0`. Consequently, cosine distance simplifies to a simple dot product, reducing query computational complexity.

### 2. Database Index
To query hundreds of thousands of vectors efficiently, we leverage the **HNSW (Hierarchical Navigable Small World)** index. The index is defined on `asset_chunks.embedding` using the `vector_cosine_ops` operator class:
```sql
CREATE INDEX idx_asset_chunks_embedding 
ON asset_chunks 
USING hnsw (embedding vector_cosine_ops);
```

## Flow of Execution

When querying similar chunks, `SemanticSearchRepository` issues an async query joining the `Asset` and `AssetChunk` models:
```python
distance = AssetChunk.embedding.cosine_distance(query_vector)
stmt = select(...).join(Asset).order_by(distance.asc()).limit(limit)
```
1. Postgres traverses the HNSW graph starting from the top layer down to the nearest-neighbor list.
2. Filter conditions (e.g. `Asset.modality`) are applied during scanning.
3. Chunks with `NULL` embeddings are bypassed.
4. The database returns the matching chunk rows along with their raw cosine similarity (`1.0 - distance`).

## Tradeoffs

- **HNSW Index Parameters**: HNSW provides rapid search times (< 10ms for search graph traversal) but requires more memory and takes longer to construct compared to IVFFlat indexes.
- **Index Precision**: Approximate Nearest Neighbors (ANN) searching through HNSW trade off perfect recall for speed. With high graph parameter settings, search recall exceeds 95-98%.

## Future Improvements

- **Tune Graph Settings**: Adjust HNSW parameters like `m` and `ef_construction` during database setup depending on production data size.
- **Query Optimization**: Tune pgvector session parameter `hnsw.ef_search` dynamically depending on performance and precision requirements.
