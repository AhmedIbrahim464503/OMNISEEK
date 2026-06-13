import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class ModalityEnum(str, enum.Enum):
    """Supported multi-modal media asset modalities."""
    
    TEXT = "TEXT"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"

class Asset(Base):
    """Parent database model representing an uploaded multi-modal media file asset."""

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    modality: Mapped[ModalityEnum] = mapped_column(Enum(ModalityEnum), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Establish parent-to-child cascading relationship with chunks
    chunks = relationship("AssetChunk", back_populates="asset", cascade="all, delete-orphan")
