"""
Generic BaseRepository.

This base class implements standard CRUD (Create, Read, Update, Delete)
operations using Python Generics.

By inheriting from this, specific repositories (like DocumentRepository)
get these standard methods for free, and only need to implement their
custom, domain-specific queries.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.base import Base

# ModelType is a generic type variable bound to our declarative Base.
# This tells type checkers that ModelType must be an ORM model.
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: Session):
        """
        Initialize the repository.
        
        Args:
            model: The SQLAlchemy model class (e.g., Document).
            db: The database session.
        """
        self.model = model
        self.db = db

    def get_by_id(self, id: UUID) -> ModelType | None:
        """Fetch a single record by its UUID primary key."""
        return self.db.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Fetch a paginated list of records."""
        stmt = select(self.model).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new record.
        
        Note: The object is added to the session but the session is NOT
        committed here. The caller (e.g., a service or route handler)
        should call db.commit() when the logical transaction is complete.
        """
        obj = self.model(**kwargs)
        self.db.add(obj)
        # Flush sends the INSERT to the database so we get an ID back,
        # but it doesn't commit the transaction.
        self.db.flush()
        return obj

    def update(self, id: UUID, **kwargs: Any) -> ModelType | None:
        """
        Update an existing record by ID.
        """
        obj = self.get_by_id(id)
        if not obj:
            return None

        for key, value in kwargs.items():
            setattr(obj, key, value)
            
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, id: UUID) -> bool:
        """
        Delete a record by ID.
        Returns True if deleted, False if not found.
        """
        obj = self.get_by_id(id)
        if not obj:
            return False
            
        self.db.delete(obj)
        self.db.flush()
        return True
