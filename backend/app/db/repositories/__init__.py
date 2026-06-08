"""
Repository layer.

The repository pattern abstracts database operations behind a clean,
domain-specific API.

Why use repositories?
  - Your route handlers shouldn't know about SQLAlchemy or SQL.
  - They keep data access logic in one place (DRY).
  - They make unit testing route handlers much easier (you can mock
    the repository instead of mocking a database session).
"""

from backend.app.db.repositories.base_repository import BaseRepository
from backend.app.db.repositories.chunk_repository import ChunkRepository
from backend.app.db.repositories.document_repository import DocumentRepository

__all__ = [
    "BaseRepository",
    "ChunkRepository",
    "DocumentRepository",
]
