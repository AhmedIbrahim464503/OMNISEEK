import sys
from unittest.mock import MagicMock

# Mock ML modules
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['pillow'] = MagicMock()
mock_pil = MagicMock()
mock_pil.__version__ = "10.2.0"
sys.modules['PIL'] = mock_pil

import unittest
from unittest.mock import AsyncMock, patch
import time
from fastapi import HTTPException, status

# Set up path imports
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth import AuthService
from services.cache import CacheService
from services.task_status import TaskStatusService
from api.rate_limiter import RateLimiter
from api.metrics import metrics_collector
from models.user import User
from models.task_status import TaskStatus

class TestAuthService(unittest.TestCase):
    """Test verification of AuthService credentials hashing and JWT verification."""

    def test_password_hashing_and_verification(self):
        password = "secretpassword123"
        hashed = AuthService.hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(AuthService.verify_password(password, hashed))
        self.assertFalse(AuthService.verify_password("wrongpassword", hashed))

    def test_jwt_token_generation_and_decoding(self):
        username = "admin"
        role = "ADMIN"
        token = AuthService.create_access_token(username, role)
        
        self.assertIsNotNone(token)
        payload = AuthService.decode_access_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], username)
        self.assertEqual(payload["role"], role)
        
    def test_invalid_jwt_verification(self):
        invalid_token = "header.payload.signature"
        payload = AuthService.decode_access_token(invalid_token)
        self.assertIsNone(payload)

class TestCacheService(unittest.IsolatedAsyncioTestCase):
    """Test case verifying Redis cache operations and glob pattern invalidations."""

    @patch("services.cache.CacheService.get_client")
    async def test_cache_get_and_set(self, mock_client_fn):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"cached": "data"}'
        mock_client_fn.return_value = mock_redis

        # Set value
        await CacheService.set("key1", {"cached": "data"}, ttl=60)
        mock_redis.set.assert_called_once_with("key1", '{"cached": "data"}', ex=60)

        # Get value
        val = await CacheService.get("key1")
        self.assertEqual(val, {"cached": "data"})
        mock_redis.get.assert_called_once_with("key1")

    @patch("services.cache.CacheService.get_client")
    async def test_cache_glob_invalidation(self, mock_client_fn):
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["search:q1", "search:q2"]
        mock_client_fn.return_value = mock_redis

        await CacheService.invalidate_pattern("search:*")
        mock_redis.keys.assert_called_once_with("search:*")
        mock_redis.delete.assert_called_once_with("search:q1", "search:q2")

class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    """Test case verifying Redis bucket increments and 429 HTTP errors."""

    @patch("services.cache.CacheService.get_client")
    async def test_rate_limiter_exceed_throws_429(self, mock_client_fn):
        mock_redis = AsyncMock()
        # Mock count returning 11 (greater than limit 10)
        mock_redis.incr.return_value = 11
        mock_client_fn.return_value = mock_redis

        limiter = RateLimiter("test_limit", limit=10, window_seconds=60)
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        with self.assertRaises(HTTPException) as ctx:
            await limiter(mock_request)
            
        self.assertEqual(ctx.exception.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @patch("services.cache.CacheService.get_client")
    async def test_rate_limiter_bypass_on_redis_error(self, mock_client_fn):
        mock_client_fn.side_effect = Exception("Redis Down")
        
        limiter = RateLimiter("test_limit", limit=10, window_seconds=60)
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        # Rate limiter should log warning and bypass without throwing exception
        await limiter(mock_request)

class TestTaskStatusService(unittest.IsolatedAsyncioTestCase):
    """Test case verifying database-backed Celery task registration and updates."""

    async def test_db_create_and_update_tasks(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        
        # Test creation
        task = await TaskStatusService.create_task_status(mock_db, "task-1", "process_embeddings")
        self.assertEqual(task.id, "task-1")
        self.assertEqual(task.status, "PENDING")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Reset mocks
        mock_db.reset_mock()
        
        # Mock fetch returning the task status
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = task
        mock_db.execute.return_value = mock_result
        
        # Test status updates
        updated_task = await TaskStatusService.update_task_status(
            db=mock_db,
            task_id="task-1",
            status="SUCCESS",
            result={"status": "completed"}
        )
        self.assertEqual(updated_task.status, "SUCCESS")
        self.assertEqual(updated_task.result, {"status": "completed"})
        mock_db.commit.assert_called_once()

class TestMetricsCollector(unittest.TestCase):
    """Test case verifying Prometheus metric tracking and help descriptions."""

    def test_metrics_collection_and_formatting(self):
        collector = metrics_collector
        collector.record_request("GET", "/api/search", 200, 0.15)
        collector.record_task("workers.worker.ping", "SUCCESS")
        collector.record_db(0.045)
        collector.record_search("accurate", 0.950)
        
        prometheus_text = collector.get_prometheus_output()
        
        self.assertIn("# HELP http_requests_total", prometheus_text)
        self.assertIn("# HELP celery_tasks_total", prometheus_text)
        self.assertIn('http_requests_total{method="GET",path="/api/search",status="200"}', prometheus_text)
        self.assertIn('celery_tasks_total{name="workers.worker.ping",status="SUCCESS"}', prometheus_text)
        self.assertIn("db_query_duration_seconds_avg", prometheus_text)
        self.assertIn('search_latency_seconds_avg{mode="accurate"}', prometheus_text)
