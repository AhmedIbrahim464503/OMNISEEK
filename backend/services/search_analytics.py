from sqlalchemy.ext.asyncio import AsyncSession
from models.search_log import SearchLog
from core.logging import logger

class SearchAnalyticsService:
    """Service to track search queries, execution latency, and results counts for observability."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log_search(self, query: str, latency_ms: float, results_count: int) -> SearchLog:
        """
        Record search operation metrics inside the search_logs table.
        """
        try:
            log_entry = SearchLog(
                query=query,
                latency_ms=latency_ms,
                results_count=results_count
            )
            self.db.add(log_entry)
            await self.db.commit()
            return log_entry
        except Exception as e:
            logger.error(f"Search analytics logging failed: {str(e)}")
            await self.db.rollback()
            raise e
