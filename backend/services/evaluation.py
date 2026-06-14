import math
from typing import Any, Dict, List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from models.evaluation_run import EvaluationRun
from core.logging import logger

class EvaluationService:
    """Service calculating search quality metrics and persisting them to the database."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def calculate_metrics(
        results: List[Dict[str, Any]],
        ground_truth: Set[str],
        k: int = 5
    ) -> Dict[str, float]:
        """
        Computes search quality metrics (Precision@K, Recall@K, MRR, NDCG, Accuracy@K)
        given a set of retrieved results and ground truth asset names/IDs.
        """
        top_k_results = results[:k]
        if not ground_truth:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "mrr": 0.0,
                "ndcg": 0.0,
                "accuracy": 0.0
            }

        # 1. Binary relevance array for the top K retrieved results
        relevance = [
            1.0 if item.get("asset_name") in ground_truth or item.get("asset_id") in ground_truth else 0.0
            for item in top_k_results
        ]

        # 2. Precision@K
        relevant_retrieved = sum(relevance)
        precision = relevant_retrieved / k if k > 0 else 0.0

        # 3. Recall@K
        total_relevant = len(ground_truth)
        recall = relevant_retrieved / total_relevant if total_relevant > 0 else 0.0

        # 4. Mean Reciprocal Rank (MRR)
        mrr = 0.0
        for idx, rel in enumerate(relevance):
            if rel == 1.0:
                mrr = 1.0 / (idx + 1)
                break

        # 5. NDCG
        dcg = 0.0
        for idx, rel in enumerate(relevance):
            dcg += rel / math.log2(idx + 2)

        idcg = 0.0
        # Calculate Ideal DCG for the top min(k, total_relevant) spots
        for idx in range(min(k, total_relevant)):
            idcg += 1.0 / math.log2(idx + 2)

        ndcg = dcg / idcg if idcg > 0.0 else 0.0

        # 6. Accuracy@K
        accuracy = 1.0 if relevant_retrieved > 0 else 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "mrr": round(mrr, 4),
            "ndcg": round(ndcg, 4),
            "accuracy": round(accuracy, 4)
        }

    async def log_evaluation_metrics(
        self,
        query: str,
        metrics: Dict[str, float]
    ) -> List[EvaluationRun]:
        """
        Persist metrics to the evaluation_runs table in the database.
        """
        entries = []
        try:
            for name, val in metrics.items():
                run_entry = EvaluationRun(
                    query=query,
                    metric_name=name,
                    metric_value=val
                )
                self.db.add(run_entry)
                entries.append(run_entry)
            await self.db.commit()
            return entries
        except Exception as e:
            logger.error(f"Failed to record evaluation metrics: {str(e)}")
            await self.db.rollback()
            raise e
