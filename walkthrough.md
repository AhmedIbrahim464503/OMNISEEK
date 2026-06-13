# Phase 2 Walkthrough: Database Design, Vector Architecture, and Schema Implementation

This document outlines the database tables design, SQLAlchemy models, repository classes, database service wrapper, setup guide, and testing scripts implemented in Phase 2.

---

## 1. Updated Folder Structure

The repository structure has been expanded with database models, repositories, and services:

```
OMNISEEK/
├── backend/
│   ├── api/
│   │   └── router.py
│   ├── core/
│   │   ├── celery.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── exceptions.py
│   │   ├── init_schema.py   <-- [NEW] Schema init script
│   │   └── logging.py
│   ├── models/
│   │   ├── __init__.py      <-- [NEW] Exposed models
│   │   ├── asset.py         <-- [NEW] Asset model
│   │   ├── base.py
│   │   └── chunk.py         <-- [NEW] AssetChunk model
│   ├── repositories/
│   │   ├── asset.py         <-- [NEW] Asset repository
│   │   ├── base.py
│   │   └── chunk.py         <-- [NEW] Chunk repository
│   ├── schemas/
│   │   └── base.py
│   ├── scratch/
│   │   └── verify_phase2.py <-- [NEW] Verification test script
│   ├── services/
│   │   ├── base.py
│   │   └── database.py      <-- [NEW] DB Service transaction wrapper
│   ├── workers/
│   │   └── worker.py
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   └── README.md
├── .env
├── .env.example
└── docker-compose.yml
```

---

## 2. Implemented Code Files

### [asset.py (models)](file:///d:/projects/sps_project/backend/models/asset.py)
SQLAlchemy model mapping the `assets` table.
```python
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
```

### [chunk.py (models)](file:///d:/projects/sps_project/backend/models/chunk.py)
SQLAlchemy model mapping the `asset_chunks` table, containing a 512-dimension pgvector and HNSW index optimized for cosine similarity.
```python
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
```

### [__init__.py (models)](file:///d:/projects/sps_project/backend/models/__init__.py)
```python
from models.base import Base
from models.asset import Asset, ModalityEnum
from models.chunk import AssetChunk

__all__ = ["Base", "Asset", "ModalityEnum", "AssetChunk"]
```

### [asset.py (repositories)](file:///d:/projects/sps_project/backend/repositories/asset.py)
```python
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset, ModalityEnum
from repositories.base import BaseRepository

class AssetRepository(BaseRepository[Asset]):
    """Repository implementation for database access operations on the Asset model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the repository binding it to the Asset model and DB session."""
        super().__init__(Asset, db)

    async def create_asset(
        self, filename: str, file_path: str, modality: ModalityEnum
    ) -> Asset:
        """Create and write a new Asset entity to the database session."""
        asset = Asset(
            filename=filename,
            file_path=file_path,
            modality=modality
        )
        self.db.add(asset)
        return asset

    async def get_asset_by_id(self, asset_id: uuid.UUID) -> Optional[Asset]:
        """Fetch an Asset database record uniquely matching the provided UUID."""
        stmt = select(Asset).filter(Asset.id == asset_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_assets(self, skip: int = 0, limit: int = 100) -> List[Asset]:
        """Fetch multiple Asset database records with standard pagination limit offsets."""
        stmt = select(Asset).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

### [chunk.py (repositories)](file:///d:/projects/sps_project/backend/repositories/chunk.py)
```python
import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset
from models.chunk import AssetChunk
from repositories.base import BaseRepository

class ChunkRepository(BaseRepository[AssetChunk]):
    """Repository implementation for database access operations on the AssetChunk model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the repository binding it to the AssetChunk model and DB session."""
        super().__init__(AssetChunk, db)

    async def insert_chunks_bulk(self, chunks_data: List[Dict[str, Any]]) -> List[AssetChunk]:
        """Bulk insert multiple AssetChunk entities into the database session."""
        chunks = [
            AssetChunk(
                asset_id=data["asset_id"],
                chunk_index=data["chunk_index"],
                content=data["content"],
                start_time=data.get("start_time"),
                end_time=data.get("end_time"),
                metadata=data.get("metadata", {}),
                embedding=data["embedding"]
            )
            for data in chunks_data
        ]
        self.db.add_all(chunks)
        return chunks

    async def search_similar_chunks(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query vector database for similar chunks using cosine distance operator."""
        distance = AssetChunk.embedding.cosine_distance(query_vector)
        stmt = (
            select(
                Asset.filename.label("asset_name"),
                Asset.file_path,
                AssetChunk.content.label("chunk_content"),
                AssetChunk.start_time,
                AssetChunk.end_time,
                (1.0 - distance).label("similarity_score")
            )
            .join(Asset, AssetChunk.asset_id == Asset.id)
            .order_by(distance.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "asset_name": row.asset_name,
                "file_path": row.file_path,
                "chunk_content": row.chunk_content,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "similarity_score": float(row.similarity_score)
            }
            for row in result.all()
        ]

    async def get_chunks_by_asset(self, asset_id: uuid.UUID) -> List[AssetChunk]:
        """Fetch all AssetChunk records associated with a parent Asset UUID."""
        stmt = (
            select(AssetChunk)
            .filter(AssetChunk.asset_id == asset_id)
            .order_by(AssetChunk.chunk_index.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
```

### [database.py (services)](file:///d:/projects/sps_project/backend/services/database.py)
```python
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset, ModalityEnum
from models.chunk import AssetChunk
from repositories.asset import AssetRepository
from repositories.chunk import ChunkRepository
from core.exceptions import DatabaseError

class DatabaseService:
    """Service wrapper managing transactions and database repository executions."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the service binding it to an active DB session and repo instances."""
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.chunk_repo = ChunkRepository(db)

    async def create_asset(
        self, filename: str, file_path: str, modality: ModalityEnum
    ) -> Asset:
        """Persist a new media asset context within a committed transactional block."""
        try:
            asset = await self.asset_repo.create_asset(filename, file_path, modality)
            await self.db.commit()
            await self.db.refresh(asset)
            return asset
        except Exception as err:
            await self.db.rollback()
            raise DatabaseError(f"Failed to create asset: {str(err)}") from err

    async def get_asset_by_id(self, asset_id: uuid.UUID) -> Optional[Asset]:
        """Fetch a single Asset record uniquely matching the provided UUID."""
        try:
            return await self.asset_repo.get_asset_by_id(asset_id)
        except Exception as err:
            raise DatabaseError(f"Failed to retrieve asset: {str(err)}") from err

    async def list_assets(self, skip: int = 0, limit: int = 100) -> List[Asset]:
        """Fetch multiple Asset records with standard pagination limit offsets."""
        try:
            return await self.asset_repo.list_assets(skip=skip, limit=limit)
        except Exception as err:
            raise DatabaseError(f"Failed to list assets: {str(err)}") from err

    async def add_asset_chunks(
        self, chunks_data: List[Dict[str, Any]]
    ) -> List[AssetChunk]:
        """Bulk insert and commit chunks for a given asset within a transaction."""
        try:
            chunks = await self.chunk_repo.insert_chunks_bulk(chunks_data)
            await self.db.commit()
            return chunks
        except Exception as err:
            await self.db.rollback()
            raise DatabaseError(f"Failed to insert asset chunks: {str(err)}") from err

    async def search_similar_chunks(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query vector database for similar chunks using cosine similarity scoring."""
        try:
            return await self.chunk_repo.search_similar_chunks(query_vector, limit)
        except Exception as err:
            raise DatabaseError(f"Vector similarity search failed: {str(err)}") from err

    async def get_chunks_by_asset(self, asset_id: uuid.UUID) -> List[AssetChunk]:
        """Fetch all chunks related to an asset UUID."""
        try:
            return await self.chunk_repo.get_chunks_by_asset(asset_id)
        except Exception as err:
            raise DatabaseError(f"Failed to get chunks for asset: {str(err)}") from err
```

### [init_schema.py (core)](file:///d:/projects/sps_project/backend/core/init_schema.py)
Creates pgvector extension and database schemas automatically.
```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings
from core.logging import setup_logging, logger
from core.db import init_db
from models.base import Base
from models.asset import Asset
from models.chunk import AssetChunk

async def run_init() -> None:
    """Establish postgres pgvector extension and create all declarative schemas."""
    setup_logging()
    logger.info("Initializing database extension and schema mapping...")
    
    # Enable vector extension on startup
    await init_db()
    
    # Connect and build schemas
    engine = create_async_engine(settings.DB_URL, echo=settings.DEBUG)
    async with engine.begin() as conn:
        logger.info("Creating application tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    await engine.dispose()
    logger.info("Database schema sync completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_init())
```

---

## 3. Database Initialization & Setup

To deploy the schema updates onto your Postgres container:

1. Start your Docker Compose stack (if not already running):
   ```bash
   docker-compose up -d
   ```
2. Run the initialization script inside the `backend` container to enable `pgvector` and register schemas:
   ```bash
   docker-compose exec backend python core/init_schema.py
   ```
3. Verify that the tables `assets` and `asset_chunks` have been created and the index `idx_asset_chunks_embedding` is registered.

---

## 4. Verification & Testing

### Executing Compilation Checks
Run the syntax check on the codebase:
```bash
python -m py_compile backend/models/*.py backend/repositories/*.py backend/services/*.py backend/core/init_schema.py backend/scratch/verify_phase2.py
```

### Running Vector Similarity Queries Test
We have provided a comprehensive verification script at `backend/scratch/verify_phase2.py`.

To execute the test suite:
1. Run the test script inside the backend container context:
   ```bash
   docker-compose exec backend python scratch/verify_phase2.py
   ```
2. The verification script executes:
   - Insertion of a mock `VIDEO` asset (`sample_presentation.mp4`).
   - Bulk insertion of two mock chunks with distinct 512-dimension vector embeddings.
   - Nearest-neighbor similarity search (using a mock query vector).
   - Assertion testing on join outputs and scores.
