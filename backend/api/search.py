from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_db
from core.logging import logger
from services.search import SearchService
from services.benchmark import SearchBenchmarkService
from models.performance_log import SearchPerformanceLog
from models.evaluation_run import EvaluationRun
from models.search_log import SearchLog

router = APIRouter()

@router.get("/search", tags=["Search"])
async def search(
    q: str = Query(..., description="Query string for semantic search"),
    modality: Optional[str] = Query(None, description="Optional modality filter: TEXT, AUDIO, VIDEO"),
    mode: str = Query("fast", description="Search profile mode: fast, balanced, accurate"),
    top_k: int = Query(20, description="Max number of candidate chunks to retrieve"),
    minimum_score: float = Query(0.30, description="Minimum quality score threshold (0.0 to 1.0)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Unified multi-modal search endpoint.
    Supports Fast (vector), Balanced (hybrid), and Accurate (hybrid + reranked) profiles,
    returning explanations and detailed latency metrics.
    """
    logger.info(f"API search request received: q='{q}', mode={mode}, modality={modality}, top_k={top_k}, minimum_score={minimum_score}")
    
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty or whitespace.")

    if mode not in ["fast", "balanced", "accurate"]:
        raise HTTPException(status_code=400, detail="Search profile 'mode' must be one of: fast, balanced, accurate.")

    try:
        search_service = SearchService(db)
        results = await search_service.execute_search(
            query=q,
            limit=top_k,
            modality=modality,
            mode=mode,
            minimum_score=minimum_score
        )
        return results
    except Exception as e:
        logger.error(f"Error executing search route: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search service error: {str(e)}")

@router.post("/search/benchmark", tags=["Search"])
async def run_benchmark(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Triggers the benchmarking suite running queries across search modes,
    generating comparative quality reports.
    """
    logger.info("API trigger search benchmarking invoked.")
    try:
        benchmark_service = SearchBenchmarkService(db)
        report = await benchmark_service.run_benchmark_suite()
        return report
    except Exception as e:
        logger.error(f"Error executing benchmark suite: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Benchmarking error: {str(e)}")

@router.get("/search/dashboard", tags=["Search"])
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Retrieves database-backed analytics and metrics summarizing retrieval quality and latencies.
    Consumed by downstream analytics dashboards.
    """
    logger.info("API request for search quality dashboard metrics received.")
    try:
        # 1. Average Latency (from search_performance_logs)
        avg_latency_stmt = select(func.avg(SearchPerformanceLog.total_ms))
        avg_lat_res = await db.execute(avg_latency_stmt)
        avg_latency = float(avg_lat_res.scalar() or 0.0)

        # 2. Average Precision, Recall, MRR, NDCG (from evaluation_runs)
        avg_metrics_stmt = select(
            EvaluationRun.metric_name,
            func.avg(EvaluationRun.metric_value)
        ).group_by(EvaluationRun.metric_name)
        avg_met_res = await db.execute(avg_metrics_stmt)
        avg_metrics = {row[0]: round(float(row[1]), 4) for row in avg_met_res.all()}

        # 3. Most Frequent Queries (from search_logs)
        freq_queries_stmt = select(
            SearchLog.query,
            func.count(SearchLog.id)
        ).group_by(SearchLog.query).order_by(desc(func.count(SearchLog.id))).limit(5)
        freq_res = await db.execute(freq_queries_stmt)
        frequent_queries = [{"query": row[0], "count": row[1]} for row in freq_res.all()]

        # 4. Lowest Performing Queries (queries with lowest average results count)
        low_perf_stmt = select(
            SearchLog.query,
            func.avg(SearchLog.results_count)
        ).group_by(SearchLog.query).order_by(func.avg(SearchLog.results_count).asc()).limit(5)
        low_res = await db.execute(low_perf_stmt)
        low_performing_queries = [{"query": row[0], "avg_results": float(row[1])} for row in low_res.all()]

        # 5. Most Successful Queries (queries with highest average results count)
        high_perf_stmt = select(
            SearchLog.query,
            func.avg(SearchLog.results_count)
        ).group_by(SearchLog.query).order_by(desc(func.avg(SearchLog.results_count))).limit(5)
        high_res = await db.execute(high_perf_stmt)
        successful_queries = [{"query": row[0], "avg_results": float(row[1])} for row in high_res.all()]

        return {
            "average_latency_ms": round(avg_latency, 2),
            "retrieval_effectiveness": avg_metrics,
            "frequent_queries": frequent_queries,
            "successful_queries": successful_queries,
            "lowest_performing_queries": low_performing_queries
        }
    except Exception as e:
        logger.error(f"Error compiling search dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard telemetry error: {str(e)}")
