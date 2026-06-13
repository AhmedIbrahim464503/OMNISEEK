from typing import Generic, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Generic repository implementation encapsulating database access patterns."""

    def __init__(self, model: Type[ModelType], db: AsyncSession) -> None:
        """Initialize the repository with a specific SQLAlchemy model and session."""
        self.model = model
        self.db = db
