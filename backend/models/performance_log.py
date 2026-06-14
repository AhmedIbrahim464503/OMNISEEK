import uuid
from datetime import datetime
from sqlalchemy import DateTime, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class SearchPerformanceLog(Base):
    """Database model storing detailed execution latency breakdowns (retrieval vs. reranking vs. total latency)."""

    __tablename__ = "search_performance_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_ms: Mapped[float] = mapped_column(Float, nullable=False)
    rerank_ms: Mapped[float] = mapped_column(Float, nullable=False)
    total_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
