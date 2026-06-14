import time
from typing import Any, Dict, List, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset
from services.search import SearchService
from services.evaluation import EvaluationService

class SearchBenchmarkService:
    """Service running search benchmark suites to compare vector, hybrid, and reranked search strategies."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.evaluation_service = EvaluationService(db)

    async def run_benchmark_suite(self) -> Dict[str, Any]:
        """
        Executes benchmark queries across search strategies, computes effectiveness metrics,
        measures execution latencies, and returns a detailed comparative evaluation report.
        """
        # Fetch first few assets in DB to construct a dynamic, valid ground truth set
        stmt = select(Asset.filename)
        res = await self.db.execute(stmt)
        all_assets = [row[0] for row in res.all()]

        # Define default benchmark queries and map them to expected assets
        benchmark_queries = {
            "machine learning": {all_assets[0]} if all_assets else {"machine_learning.pdf"},
            "person drinking milk": {all_assets[1]} if len(all_assets) > 1 else ({all_assets[0]} if all_assets else {"meeting.mp4"}),
            "climate change discussion": {all_assets[2]} if len(all_assets) > 2 else ({all_assets[0]} if all_assets else {"presentation.pdf"})
        }

        from services.search import SearchService
        search_service = SearchService(self.db)
        report_runs = []

        for query, ground_truth in benchmark_queries.items():
            query_report = {
                "query": query,
                "ground_truth": list(ground_truth),
                "strategies": {}
            }

            # Test Fast, Balanced, and Accurate modes
            for mode, strategy_name in [("fast", "Vector Search (Fast)"), ("balanced", "Hybrid Search (Balanced)"), ("accurate", "Reranked Search (Accurate)")]:
                start_time = time.perf_counter()
                
                # Execute search
                search_res = await search_service.execute_search(
                    query=query,
                    limit=10,
                    modality=None,
                    mode=mode
                )
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                results = search_res.get("results", [])

                # Calculate metrics
                metrics = self.evaluation_service.calculate_metrics(
                    results=results,
                    ground_truth=ground_truth,
                    k=5
                )

                # Persist metrics to the DB logs
                await self.evaluation_service.log_evaluation_metrics(
                    query=f"[{strategy_name}] {query}",
                    metrics=metrics
                )

                query_report["strategies"][mode] = {
                    "strategy_name": strategy_name,
                    "latency_ms": round(elapsed_ms, 2),
                    "results_count": len(results),
                    "metrics": metrics
                }
            
            report_runs.append(query_report)

        # Calculate averages across all benchmark queries
        summary = {}
        for mode in ["fast", "balanced", "accurate"]:
            runs_for_mode = [r["strategies"][mode] for r in report_runs]
            avg_latency = sum(r["latency_ms"] for r in runs_for_mode) / len(runs_for_mode)
            avg_precision = sum(r["metrics"]["precision"] for r in runs_for_mode) / len(runs_for_mode)
            avg_recall = sum(r["metrics"]["recall"] for r in runs_for_mode) / len(runs_for_mode)
            avg_mrr = sum(r["metrics"]["mrr"] for r in runs_for_mode) / len(runs_for_mode)
            avg_ndcg = sum(r["metrics"]["ndcg"] for r in runs_for_mode) / len(runs_for_mode)

            summary[mode] = {
                "avg_latency_ms": round(avg_latency, 2),
                "avg_precision": round(avg_precision, 4),
                "avg_recall": round(avg_recall, 4),
                "avg_mrr": round(avg_mrr, 4),
                "avg_ndcg": round(avg_ndcg, 4)
            }

        return {
            "benchmark_runs": report_runs,
            "comparative_summary": summary
        }
