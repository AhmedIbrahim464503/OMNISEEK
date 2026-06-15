import sys
from unittest.mock import MagicMock

# Inject mock modules for heavy ML frameworks to allow test execution on host without torch/transformers/etc.
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['pillow'] = MagicMock()
mock_pil = MagicMock()
mock_pil.__version__ = "10.2.0"
sys.modules['PIL'] = mock_pil

import unittest
import numpy as np
from unittest.mock import AsyncMock, patch
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

# Import models & services
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.search_log import SearchLog
from models.evaluation_run import EvaluationRun
from models.performance_log import SearchPerformanceLog
from models.asset import ModalityEnum, Asset
from models.chunk import AssetChunk
from repositories.search import SemanticSearchRepository
from services.search_embedding import SearchEmbeddingService
from services.search_analytics import SearchAnalyticsService
from services.search import ScoreNormalizer, DuplicateResultFilter, ResultAggregator, SearchService
from services.reranker import RerankerService
from services.hybrid_search import HybridSearchService
from services.explainability import ExplainabilityService
from services.evaluation import EvaluationService
from services.benchmark import SearchBenchmarkService
from services.quality_filter import ResultQualityFilter


class TestRerankerService(unittest.TestCase):
    """Test suite verifying reranker service predictions and logits sigmoid mapping."""

    @patch("services.reranker.AIModelManager")
    def test_rerank_candidates_sorting_and_activation(self, mock_manager_cls):
        # Setup mock reranker model returning logits
        mock_model = MagicMock()
        # Logits of 1.0 (highly relevant) and -2.0 (non-relevant)
        mock_model.predict.return_value = np.array([1.0, -2.0])
        
        mock_manager = MagicMock()
        mock_manager.reranker_model = mock_model
        mock_manager_cls.return_value = mock_manager

        candidates = [
            {"chunk_id": "c1", "content": "hello", "score": 0.5},
            {"chunk_id": "c2", "content": "world", "score": 0.6}
        ]

        reranked = RerankerService.rerank_candidates("query text", candidates, top_k=2)

        # Verify correct length
        self.assertEqual(len(reranked), 2)
        # c1 logit is 1.0 -> Sigmoid(1.0) = 1/(1+e^-1) = 0.731
        # c2 logit is -2.0 -> Sigmoid(-2.0) = 1/(1+e^2) = 0.119
        # So c1 should be sorted first
        self.assertEqual(reranked[0]["chunk_id"], "c1")
        self.assertAlmostEqual(reranked[0]["score"], 0.73105857863)
        self.assertAlmostEqual(reranked[1]["score"], 0.11920292202)
        
        # Verify vector_score was mapped
        self.assertEqual(reranked[0]["vector_score"], 0.5)
        self.assertEqual(reranked[1]["vector_score"], 0.6)


class TestHybridSearchService(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying hybrid search candidate retrieval and score fusion."""

    async def test_execute_hybrid_search_fusion(self):
        mock_repo = MagicMock(spec=SemanticSearchRepository)
        
        # Vector results (semantic_score = 0.8)
        vector_task = AsyncMock(return_value=[
            {"chunk_id": "chunk-1", "asset_id": "a1", "asset_name": "t1.txt", "modality": "TEXT", "chunk_index": 0, "content": "data science", "score": 0.8}
        ])
        # Keyword results (keyword_score = 0.6)
        keyword_task = AsyncMock(return_value=[
            {"chunk_id": "chunk-1", "asset_id": "a1", "asset_name": "t1.txt", "modality": "TEXT", "chunk_index": 0, "content": "data science", "score": 0.6},
            {"chunk_id": "chunk-2", "asset_id": "a1", "asset_name": "t1.txt", "modality": "TEXT", "chunk_index": 1, "content": "keyword only", "score": 0.5}
        ])
        
        mock_repo.search_similar_chunks = vector_task
        mock_repo.search_keyword_chunks = keyword_task

        hybrid_service = HybridSearchService(mock_repo)
        fused = await hybrid_service.execute_hybrid_search(
            query_text="data science",
            query_vector=[0.1] * 512,
            limit=5,
            semantic_weight=0.7,
            keyword_weight=0.3
        )

        # We expect 2 merged results
        self.assertEqual(len(fused), 2)
        
        # chunk-1 is in both: score = (0.9 * 0.7) + (0.6 * 0.3) = 0.63 + 0.18 = 0.81
        chunk_1 = next(item for item in fused if item["chunk_id"] == "chunk-1")
        self.assertAlmostEqual(chunk_1["score"], 0.81)
        self.assertEqual(chunk_1["semantic_score"], 0.9)
        self.assertEqual(chunk_1["keyword_score"], 0.6)

        # chunk-2 is in keyword only: score = (0.0 * 0.7) + (0.5 * 0.3) = 0.15
        chunk_2 = next(item for item in fused if item["chunk_id"] == "chunk-2")
        self.assertAlmostEqual(chunk_2["score"], 0.15)
        self.assertEqual(chunk_2["semantic_score"], 0.0)
        self.assertEqual(chunk_2["keyword_score"], 0.5)


class TestExplainabilityService(unittest.TestCase):
    """Test suite verifying explainability match text generator."""

    def test_explain_matches(self):
        chunk = {
            "chunk_id": "c1",
            "asset_name": "report.pdf",
            "modality": "TEXT",
            "semantic_score": 0.85,
            "keyword_score": 0.40,
            "score": 0.715
        }

        exp_fast = ExplainabilityService.generate_explanation("test query", chunk, "Fast (Vector Only)")
        exp_bal = ExplainabilityService.generate_explanation("test query", chunk, "Balanced (Hybrid)")
        
        self.assertIn("semantic match", exp_fast.lower())
        self.assertIn("strong match", exp_bal.lower())
        self.assertIn("report.pdf", exp_fast)
        self.assertIn("report.pdf", exp_bal)


class TestEvaluationService(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying retrieval metrics precision, recall, MRR, and NDCG."""

    def test_calculate_metrics_correctness(self):
        results = [
            {"asset_name": "machine_learning.pdf"},
            {"asset_name": "other.pdf"},
            {"asset_name": "neural_networks.pdf"}
        ]
        
        ground_truth = {"machine_learning.pdf", "neural_networks.pdf"}
        
        # Calculate top-2 metrics
        metrics = EvaluationService.calculate_metrics(results, ground_truth, k=2)

        # Top 2 results: ML (relevant), other (irrelevant)
        # Precision@2 = 1/2 = 0.5
        self.assertAlmostEqual(metrics["precision"], 0.5)
        
        # Recall@2 = 1 / 2 = 0.5 (since ground truth has 2 relevant items)
        self.assertAlmostEqual(metrics["recall"], 0.5)
        
        # MRR: first relevant is at rank 1 -> MRR = 1/1 = 1.0
        self.assertAlmostEqual(metrics["mrr"], 1.0)
        
        # DCG@2 = 1/log2(2) + 0/log2(3) = 1.0
        # IDCG@2 = 1/log2(2) + 1/log2(3) = 1 + 0.6309 = 1.6309
        # NDCG@2 = 1.0 / 1.6309 = 0.6131
        self.assertAlmostEqual(metrics["ndcg"], 0.6131, places=3)
        
        # Accuracy@2 = at least 1 relevant item = 1.0
        self.assertAlmostEqual(metrics["accuracy"], 1.0)

    async def test_log_evaluation_metrics_db(self):
        mock_db = MagicMock(spec=AsyncSession)
        eval_service = EvaluationService(mock_db)

        metrics = {"ndcg": 0.85, "precision": 0.60}
        entries = await eval_service.log_evaluation_metrics("test query", metrics)

        self.assertEqual(len(entries), 2)
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()


class TestResultQualityFilter(unittest.TestCase):
    """Test suite verifying result quality thresholds and near-duplicates pruning."""

    def test_filter_results_threshold_and_duplicates(self):
        results = [
            {"chunk_id": "c1", "content": "This is a unique chunk discussing machine learning.", "score": 0.85},
            # Near duplicate of c1 (score is lower, so should be pruned)
            {"chunk_id": "c2", "content": "This is a unique chunk discussing machine learning!!!", "score": 0.80},
            # Score below threshold (should be pruned)
            {"chunk_id": "c3", "content": "Low scoring document.", "score": 0.20},
            {"chunk_id": "c4", "content": "Entirely different content discussing neural nets.", "score": 0.75}
        ]

        filtered = ResultQualityFilter.filter_results(results, minimum_score=0.30)

        # Expected: c1 (kept), c2 (pruned as duplicate), c3 (pruned by score), c4 (kept)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["chunk_id"], "c1")
        self.assertEqual(filtered[1]["chunk_id"], "c4")


class TestSearchBenchmarkService(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying search benchmark execution returns tabular summaries."""

    @patch("services.benchmark.SearchService.execute_search", new_callable=AsyncMock)
    async def test_run_benchmark_suite(self, mock_execute_search):
        mock_db = MagicMock(spec=AsyncSession)
        
        # Setup mock db query return for assets
        mock_execute_res = MagicMock()
        mock_execute_res.all.return_value = [("sample_file.pdf",)]
        mock_db.execute = AsyncMock(return_value=mock_execute_res)

        # Mock search service execution responses
        mock_execute_search.return_value = {
            "query": "query",
            "results": [{"asset_name": "sample_file.pdf", "score": 0.85}]
        }

        benchmark_service = SearchBenchmarkService(mock_db)
        report = await benchmark_service.run_benchmark_suite()

        self.assertIn("benchmark_runs", report)
        self.assertIn("comparative_summary", report)
        
        # Verify summaries for accurate mode are computed
        self.assertIn("accurate", report["comparative_summary"])
        self.assertGreater(report["comparative_summary"]["accurate"]["avg_precision"], 0.0)


class TestSearchService(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying execution profiles and performance logs."""

    @patch("services.search.CacheService.get", new_callable=AsyncMock)
    @patch("services.search.SearchEmbeddingService.generate_query_embedding")
    @patch("services.search.SemanticSearchRepository.search_similar_chunks")
    @patch("services.search.SearchAnalyticsService.log_search")
    async def test_execute_search_fast_mode(
        self, mock_log_search, mock_search_similar_chunks, mock_generate_query_embedding, mock_cache_get
    ):
        mock_cache_get.return_value = None
        mock_db = MagicMock(spec=AsyncSession)
        mock_generate_query_embedding.return_value = [0.2] * 512
        mock_search_similar_chunks.return_value = [
            {
                "chunk_id": "c1",
                "asset_id": "a1",
                "asset_name": "clip.mp4",
                "modality": "VIDEO",
                "chunk_index": 1,
                "content": "Scene contents.",
                "start_time": 2.0,
                "end_time": 4.0,
                "score": 0.8
            }
        ]

        search_service = SearchService(mock_db)
        response = await search_service.execute_search(
            query="find clip",
            limit=10,
            mode="fast",
            minimum_score=0.1
        )

        self.assertEqual(response["strategy"], "Fast (Vector Only)")
        self.assertEqual(response["count"], 1)
        self.assertIn("results", response)
        # Latency breakdown should exist
        self.assertIn("embedding_ms", response["latency"])
        self.assertIn("retrieval_ms", response["latency"])
        
        # Verify DB insertions
        mock_db.add.assert_called_once()  # performance log entry
        mock_db.commit.assert_called_once()


class TestSearchAPI(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying routing parameters and dashboard telemetry api endpoints."""

    async def test_search_api_endpoint_modes(self):
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        mock_search_res = {
            "query": "test query",
            "strategy": "Balanced (Hybrid)",
            "count": 1,
            "latency": {"total_ms": 15.2},
            "results": [
                {
                    "asset_id": "asset-uuid-1",
                    "asset_name": "example.txt",
                    "modality": "TEXT",
                    "content": "Sample parsed text line.",
                    "start_time": None,
                    "end_time": None,
                    "score": 0.92,
                    "reason": "Test reason."
                }
            ]
        }
        
        with patch("api.search.SearchService.execute_search", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_search_res
            
            response = client.get("/api/search?q=test%20query&mode=balanced&top_k=5")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["strategy"], "Balanced (Hybrid)")
            self.assertEqual(data["results"][0]["reason"], "Test reason.")
            mock_exec.assert_called_once_with(
                query="test query",
                limit=5,
                modality=None,
                mode="balanced",
                minimum_score=0.30
            )

    async def test_search_dashboard_endpoint(self):
        from fastapi.testclient import TestClient
        from main import app
        from models.user import User
        from services.auth import get_current_user
        from core.db import get_db
        import uuid
        
        # Override auth dependency to return admin directly and bypass db check in dependency
        admin_user = User(id=uuid.uuid4(), username="admin", role="ADMIN")
        mock_db = MagicMock(spec=AsyncSession)
        
        # Configure mock_db to return counts for db.scalar
        mock_db.scalar = AsyncMock()
        mock_db.scalar.side_effect = [10, 100, 50]  # total_assets, total_chunks, total_searches
        
        mock_execute_res_1 = MagicMock()
        mock_execute_res_1.scalar.return_value = 125.4
        
        mock_execute_res_2 = MagicMock()
        mock_execute_res_2.all.return_value = [("ndcg", 0.85), ("precision", 0.70)]
        
        mock_execute_res_3 = MagicMock()
        mock_execute_res_3.all.return_value = [("query1", 5)]
        
        mock_execute_res_4 = MagicMock()
        mock_execute_res_4.all.return_value = [("query2", 0.0)]
        
        mock_execute_res_5 = MagicMock()
        mock_execute_res_5.all.return_value = [("query3", 10.0)]

        mock_db.execute = AsyncMock()
        mock_db.execute.side_effect = [
            mock_execute_res_1,
            mock_execute_res_2,
            mock_execute_res_3,
            mock_execute_res_4,
            mock_execute_res_5
        ]
        
        app.dependency_overrides[get_current_user] = lambda: admin_user
        app.dependency_overrides[get_db] = lambda: mock_db
        
        try:
            client = TestClient(app)
            response = client.get("/api/search/dashboard")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertEqual(data["average_latency_ms"], 125.4)
            self.assertEqual(data["ndcg"], 0.85)
            self.assertEqual(data["top_queries"][0]["query"], "query1")
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
