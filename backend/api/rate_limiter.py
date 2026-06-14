import time
from fastapi import Request, HTTPException, status

from services.cache import CacheService
from core.logging import logger

class RateLimiter:
    """Redis-backed rate limiting dependency for protecting API endpoints."""

    def __init__(self, key_prefix: str, limit: int, window_seconds: int = 60) -> None:
        self.key_prefix = key_prefix
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        """Execute rate check on incoming requests, raising 429 if limit exceeded."""
        # Rate limit by client IP address
        ip = request.client.host if request.client else "unknown"
        
        # Fixed window bucket calculations
        current_time = int(time.time())
        bucket = current_time // self.window_seconds
        key = f"ratelimit:{self.key_prefix}:{ip}:{bucket}"
        
        try:
            client = CacheService.get_client()
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, self.window_seconds * 2)
                
            if count > self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum allowed is {self.limit} requests per {self.window_seconds}s."
                )
        except HTTPException:
            raise
        except Exception as err:
            logger.warning(f"Rate Limiter Redis connectivity error: {str(err)}. Bypassing check.")
