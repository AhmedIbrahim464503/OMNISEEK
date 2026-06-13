import uuid
from sqlalchemy import Float, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from models.base import Base

class AssetChunk(Base):
    """Child database model representing a searchable segment/chunk of a parent asset."""

    __tablename__ = "asset_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=True)
    end_time: Mapped[float] = mapped_column(Float, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    embedding: Mapped[list] = mapped_column(Vector(512), nullable=False)

    # Establish child-to-parent relationship
    asset = relationship("Asset", back_populates="chunks")

    # Configure HNSW vector index using cosine operator class for similarity search
    __table_args__ = (
        Index(
            "idx_asset_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )
