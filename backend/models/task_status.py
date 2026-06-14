from datetime import datetime
from sqlalchemy import DateTime, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class TaskStatus(Base):
    """Database model tracking Celery background task states and completion metrics."""

    __tablename__ = "task_statuses"

    id: Mapped[str] = mapped_column(String(255), primary_key=True) # Celery Task ID
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=True)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
