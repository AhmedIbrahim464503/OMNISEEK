import uuid
from datetime import datetime
from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class EvaluationRun(Base):
    """Database model storing calculated search effectiveness metrics (e.g. Recall, Precision, MRR, NDCG)."""

    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
