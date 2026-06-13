from typing import Generic, TypeVar
from repositories.base import BaseRepository

RepoType = TypeVar("RepoType", bound=BaseRepository)

class BaseService(Generic[RepoType]):
    """Generic base class representing business logic services."""

    def __init__(self, repository: RepoType) -> None:
        """Initialize the service with its primary repository dependency."""
        self.repository = repository
