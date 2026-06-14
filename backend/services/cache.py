import json
from typing import Optional, Any
import redis.asyncio as aioredis

from core.config import settings
from core.logging import logger

class CacheService:
    """Async Redis-backed cache provider for caching queries and analytics dashboard metrics."""

    _redis: Optional[aioredis.Redis] = None

    @classmethod
    def get_client(cls) -> aioredis.Redis:
        """Retrieve or initialize the active async Redis connection client instance."""
        if cls._redis is None:
            cls._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0
            )
        return cls._redis

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Fetch deserialize JSON values from Redis cache."""
        try:
            client = cls.get_client()
            data = await client.get(key)
            if data:
                return json.loads(data)
        except Exception as err:
            logger.error(f"Cache retrieval failure for key {key}: {str(err)}")
        return None

    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = 300) -> bool:
        """Store serialized JSON values in Redis cache with configured time-to-live."""
        try:
            client = cls.get_client()
            serialized = json.dumps(value)
            await client.set(key, serialized, ex=ttl)
            return True
        except Exception as err:
            logger.error(f"Cache persistence failure for key {key}: {str(err)}")
        return False

    @classmethod
    async def delete(cls, key: str) -> bool:
        """Evict a specific key entry from Redis."""
        try:
            client = cls.get_client()
            await client.delete(key)
            return True
        except Exception as err:
            logger.error(f"Cache deletion failure for key {key}: {str(err)}")
        return False

    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> bool:
        """Invalidate all key entries matching a shell glob pattern (e.g. 'search:*')."""
        try:
            client = cls.get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
            return True
        except Exception as err:
            logger.error(f"Cache pattern invalidation failure for pattern {pattern}: {str(err)}")
        return False
