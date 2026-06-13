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
from models.asset import ModalityEnum, Asset
from models.chunk import AssetChunk
from repositories.search import SemanticSearchRepository
from services.search_embedding import SearchEmbeddingService
from services.search_analytics import SearchAnalyticsService
from services.search import ScoreNormalizer, DuplicateResultFilter, ResultAggregator, SearchService


class TestSearchEmbeddingService(unittest.TestCase):
    """Test suite verifying search embedding generation properties."""

    @patch("services.search_embedding.AIModelManager")
    def test_generate_query_embedding_success(self, mock_manager_cls):
        # Setup mock BGE-M3 model returning a 1024-dim array
        mock_model = MagicMock()
        mock_vector = np.array([0.1] * 1024)
        mock_model.encode.return_value = mock_vector
        
        mock_manager = MagicMock()
        mock_manager.bge_m3_model = mock_model
        mock_manager_cls.return_value = mock_manager

        # Generate embedding
        embedding = SearchEmbeddingService.generate_query_embedding("test query", normalize=False)
        
        # Verify it was sliced to 512 dimensions
        self.assertEqual(len(embedding), 512)
        self.assertAlmostEqual(embedding[0], 0.1)
        mock_model.encode.assert_called_once_with("test query", convert_to_numpy=True)

    @patch("services.search_embedding.AIModelManager")
    def test_generate_query_embedding_normalization(self, mock_manager_cls):
        mock_model = MagicMock()
        mock_vector = np.array([2.0] * 1024)
        mock_model.encode.return_value = mock_vector
        
        mock_manager = MagicMock()
        mock_manager.bge_m3_model = mock_model
        mock_manager_cls.return_value = mock_manager

        # Generate normalized embedding
        embedding = SearchEmbeddingService.generate_query_embedding("test query", normalize=True)
        
        # Verify L2 norm of 512 slice is 1.0
        norm = np.linalg.norm(np.array(embedding))
        self.assertAlmostEqual(norm, 1.0)

    def test_generate_query_embedding_empty_query(self):
        # Empty string query returns zero vector
        embedding = SearchEmbeddingService.generate_query_embedding("")
        self.assertEqual(len(embedding), 512)
        self.assertTrue(all(val == 0.0 for val in embedding))


class TestScoreNormalizer(unittest.TestCase):
    """Test suite verifying confidence score normalization."""

    def test_normalize_score(self):
        # Test mapping: normalized = (score + 1.0) / 2.0
        self.assertAlmostEqual(ScoreNormalizer.normalize_score(1.0), 1.0)
        self.assertAlmostEqual(ScoreNormalizer.normalize_score(-1.0), 0.0)
        self.assertAlmostEqual(ScoreNormalizer.normalize_score(0.0), 0.5)
        self.assertAlmostEqual(ScoreNormalizer.normalize_score(1.5), 1.0)
        self.assertAlmostEqual(ScoreNormalizer.normalize_score(-1.5), 0.0)


class TestDuplicateResultFilter(unittest.TestCase):
    """Test suite verifying chunk deduplication logic."""

    def test_filter_duplicates(self):
        chunks = [
            {"chunk_id": "chunk-1", "score": 0.8, "content": "hello"},
            {"chunk_id": "chunk-2", "score": 0.9, "content": "world"},
            {"chunk_id": "chunk-1", "score": 0.85, "content": "hello updated"},
        ]
        
        filtered = DuplicateResultFilter.filter_duplicates(chunks)
        self.assertEqual(len(filtered), 2)
        
        chunk_1_entry = next(c for c in filtered if c["chunk_id"] == "chunk-1")
        self.assertEqual(chunk_1_entry["score"], 0.85)
        self.assertEqual(chunk_1_entry["content"], "hello updated")


class TestResultAggregator(unittest.TestCase):
    """Test suite verifying neighboring chunk temporal aggregation."""

    def test_aggregate_neighboring_chunks(self):
        chunks = [
            {
                "chunk_id": "c1",
                "asset_id": "asset-a",
                "asset_name": "video_a.mp4",
                "modality": "VIDEO",
                "chunk_index": 0,
                "content": "First phrase.",
                "start_time": 0.0,
                "end_time": 10.0,
                "score": 0.7
            },
            {
                "chunk_id": "c2",
                "asset_id": "asset-a",
                "asset_name": "video_a.mp4",
                "modality": "VIDEO",
                "chunk_index": 1,
                "content": "Second phrase.",
                "start_time": 10.0,
                "end_time": 20.0,
                "score": 0.8
            },
            {
                "chunk_id": "c3",
                "asset_id": "asset-a",
                "asset_name": "video_a.mp4",
                "modality": "VIDEO",
                "chunk_index": 5,
                "content": "Far away phrase.",
                "start_time": 50.0,
                "end_time": 60.0,
                "score": 0.75
            },
            {
                "chunk_id": "c4",
                "asset_id": "asset-b",
                "asset_name": "audio_b.mp3",
                "modality": "AUDIO",
                "chunk_index": 0,
                "content": "Other asset.",
                "start_time": 5.0,
                "end_time": 15.0,
                "score": 0.9
            }
        ]

        results = ResultAggregator.aggregate(chunks, quality_threshold=0.0)
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["asset_name"], "audio_b.mp3")
        self.assertEqual(results[0]["score"], 0.9)

        merged_a = next(r for r in results if r["asset_name"] == "video_a.mp4" and r["score"] == 0.8)
        self.assertEqual(merged_a["content"], "First phrase. Second phrase.")
        self.assertEqual(merged_a["start_time"], 0.0)
        self.assertEqual(merged_a["end_time"], 20.0)

        isolated_a = next(r for r in results if r["asset_name"] == "video_a.mp4" and r["score"] == 0.75)
        self.assertEqual(isolated_a["content"], "Far away phrase.")
        self.assertEqual(isolated_a["start_time"], 50.0)
        self.assertEqual(isolated_a["end_time"], 60.0)

    def test_aggregate_quality_threshold(self):
        chunks = [
            {"chunk_id": "c1", "asset_id": "a1", "asset_name": "t1.txt", "modality": "TEXT", "chunk_index": 0, "content": "A", "start_time": 0.0, "end_time": 1.0, "score": 0.8},
            {"chunk_id": "c2", "asset_id": "a2", "asset_name": "t2.txt", "modality": "TEXT", "chunk_index": 0, "content": "B", "start_time": 0.0, "end_time": 1.0, "score": 0.2},
        ]
        
        results = ResultAggregator.aggregate(chunks, quality_threshold=0.5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["asset_name"], "t1.txt")


class TestSearchAnalyticsService(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying search log database insertion."""

    async def test_log_search(self):
        mock_db = MagicMock(spec=AsyncSession)
        analytics_service = SearchAnalyticsService(mock_db)

        log_entry = await analytics_service.log_search(
            query="neural network",
            latency_ms=120.5,
            results_count=10
        )

        self.assertEqual(log_entry.query, "neural network")
        self.assertEqual(log_entry.latency_ms, 120.5)
        self.assertEqual(log_entry.results_count, 10)
        
        mock_db.add.assert_called_once_with(log_entry)
        mock_db.commit.assert_called_once()


class TestSemanticSearchRepository(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying SQL statement composition and filtering."""

    async def test_search_similar_chunks_with_filters(self):
        mock_db = MagicMock(spec=AsyncSession)
        
        mock_row_1 = MagicMock()
        mock_row_1.chunk_id = "chunk-1"
        mock_row_1.asset_id = "asset-1"
        mock_row_1.asset_name = "test_file.mp4"
        mock_row_1.modality = ModalityEnum.VIDEO
        mock_row_1.chunk_index = 3
        mock_row_1.content = "Test content matching query."
        mock_row_1.start_time = 30.0
        mock_row_1.end_time = 45.0
        mock_row_1.similarity_score = 0.85

        mock_execute_res = MagicMock()
        mock_execute_res.all.return_value = [mock_row_1]
        mock_db.execute = AsyncMock(return_value=mock_execute_res)

        repository = SemanticSearchRepository(mock_db)
        
        results = await repository.search_similar_chunks(
            query_vector=[0.1] * 512,
            limit=5,
            modality="VIDEO"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["asset_name"], "test_file.mp4")
        self.assertEqual(results[0]["modality"], "VIDEO")
        self.assertEqual(results[0]["score"], 0.85)
        mock_db.execute.assert_called_once()


class TestSearchService(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying orchestration coordinates embedding, search, aggregation, and analytics logging."""

    @patch("services.search.SearchEmbeddingService.generate_query_embedding")
    @patch("services.search.SemanticSearchRepository.search_similar_chunks")
    @patch("services.search.SearchAnalyticsService.log_search")
    async def test_execute_search_orchestration(
        self, mock_log_search, mock_search_similar_chunks, mock_generate_query_embedding
    ):
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
            modality="VIDEO"
        )

        self.assertEqual(response["query"], "find clip")
        self.assertEqual(response["count"], 1)
        self.assertEqual(response["results"][0]["asset_name"], "clip.mp4")
        self.assertAlmostEqual(response["results"][0]["score"], 0.9)

        mock_generate_query_embedding.assert_called_once_with("find clip")
        mock_search_similar_chunks.assert_called_once_with(
            query_vector=[0.2] * 512, limit=10, modality="VIDEO"
        )
        mock_log_search.assert_called_once()


class TestSearchAPI(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying route requests, dependency resolution, and response validation."""

    async def test_search_api_endpoint(self):
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        mock_search_res = {
            "query": "test query",
            "count": 1,
            "results": [
                {
                    "asset_id": "asset-uuid-1",
                    "asset_name": "example.txt",
                    "modality": "TEXT",
                    "content": "Sample parsed text line.",
                    "start_time": None,
                    "end_time": None,
                    "score": 0.92
                }
            ]
        }
        
        with patch("api.search.SearchService.execute_search", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_search_res
            
            response = client.get("/api/search?q=test%20query&modality=TEXT")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["query"], "test query")
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["results"][0]["asset_name"], "example.txt")
            self.assertEqual(data["results"][0]["score"], 0.92)
            mock_exec.assert_called_once()


if __name__ == "__main__":
    unittest.main()
