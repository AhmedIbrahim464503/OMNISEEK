# Search Quality Evaluation Metrics

This document details the search evaluation metrics, mathematical formulas, and database persistence layer used to measure search quality.

## Purpose

A semantic search engine needs continuous evaluation to ensure changes to weights, thresholds, or embedding models do not degrade query quality. The evaluation framework computes standard Information Retrieval (IR) metrics to measure result relevance.

## Metric Formulations

### 1. Precision@K
Measures the proportion of retrieved documents in the top K positions that are relevant to the query:
$$Precision@K = \frac{|RelevantRetrievals \cap TopKRetrievals|}{K}$$

### 2. Recall@K
Measures the proportion of all relevant documents in the database that are successfully retrieved in the top K positions:
$$Recall@K = \frac{|RelevantRetrievals \cap TopKRetrievals|}{|TotalRelevant|}$$

### 3. Mean Reciprocal Rank (MRR)
Evaluates the rank position of the *first* relevant document returned by the search query. It is the reciprocal of the rank:
$$MRR = \frac{1}{\min_{i} (Rank_i \text{ is relevant})}$$
If no relevant document is found in the top K results, the MRR is `0.0`.

### 4. Normalized Discounted Cumulative Gain (NDCG@K)
Measures the ranking quality, discounting relevant results that appear lower down the search list:
- **DCG@K**: $\sum_{i=1}^K \frac{rel_i}{\log_2(i + 1)}$
- **IDCG@K**: Ideal DCG, calculated by sorting the top retrieved results by relevance score descending.
- **NDCG@K**: $\frac{DCG@K}{IDCG@K}$

### 5. Accuracy@K (Top-K Accuracy)
A binary metric indicating if at least one relevant document is found in the top K positions (`1.0` if relevant retrieved $\ge 1$, else `0.0`).

## Database Persistence

Evaluation metrics are saved to the `evaluation_runs` table:
- **id**: Unique UUID identifier.
- **query**: Label of query run (e.g. `[Reranked Search (Accurate)] machine learning`).
- **metric_name**: The computed metric name (e.g., `ndcg`, `precision`, `recall`).
- **metric_value**: Floating-point value of the metric.
- **created_at**: High-precision timestamp.

## Tradeoffs

- **Binary Relevance**: Currently, we use binary relevance (1 or 0) for NDCG calculations. Graded relevance (e.g., 0 to 3 for relevance levels) would provide a more detailed evaluation but requires manual relevancy grading.

## Future Improvements

- **Interactive Metric Annotator**: Build an admin interface allowing experts to run queries, tag results as relevant/irrelevant, and submit annotations to update the ground truth database.
- **Mean Average Precision (MAP)**: Compute MAP across varying query lengths for comprehensive evaluations.
