"""
Document repository.

Contains data access logic specifically for the Document model.
Inherits all basic CRUD operations from BaseRepository.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.repositories.base_repository import BaseRepository
from backend.app.models.document import Document
from backend.app.models.enums import ProcessingStatus


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: Session):
        # We explicitly pass the Document model to the base class
        super().__init__(model=Document, db=db)

    def get_by_status(self, status: ProcessingStatus | str) -> Sequence[Document]:
        """
        Fetch all documents in a specific processing stage.
        Useful for background workers picking up pending jobs.
        """
        # If passed an enum member, get its string value
        status_value = status.value if isinstance(status, ProcessingStatus) else status
        
        stmt = select(Document).where(Document.status == status_value)
        return self.db.scalars(stmt).all()

    def update_status(self, id: UUID | str, new_status: ProcessingStatus | str) -> Document | None:
        """
        Helper method to transition a document to a new pipeline stage.
        """
        db_id = UUID(id) if isinstance(id, str) else id
        status_value = new_status.value if isinstance(new_status, ProcessingStatus) else new_status
        return self.update(id=db_id, status=status_value)
