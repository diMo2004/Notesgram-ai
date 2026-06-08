"""
Chunk repository.

Contains data access logic specifically for the Chunk model.
Inherits all basic CRUD operations from BaseRepository.
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.repositories.base_repository import BaseRepository
from backend.app.models.chunk import Chunk


class ChunkRepository(BaseRepository[Chunk]):
    def __init__(self, db: Session):
        super().__init__(model=Chunk, db=db)

    def get_by_document(self, document_id: UUID) -> Sequence[Chunk]:
        """
        Retrieve all chunks for a specific document, correctly ordered.
        """
        stmt = (
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        return self.db.scalars(stmt).all()

    def bulk_create(self, document_id: UUID, chunks_data: list[dict[str, Any]]) -> Sequence[Chunk]:
        """
        Efficiently create multiple chunks for a document.
        
        Args:
            document_id: The parent document's ID.
            chunks_data: A list of dicts. Each dict should have 'content',
                         'chunk_index', and optionally 'token_count'/'embedding'.
        """
        chunks = []
        for data in chunks_data:
            chunk = Chunk(
                document_id=document_id,
                **data
            )
            chunks.append(chunk)
            
        self.db.add_all(chunks)
        self.db.flush()
        return chunks
