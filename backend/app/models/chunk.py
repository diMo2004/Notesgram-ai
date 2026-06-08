"""
Chunk ORM model.

A Chunk is a piece of text extracted from a Document.  When a user
uploads a 50-page PDF, we split it into many smaller chunks so that:

  1. Vector search finds the *right paragraph*, not the entire PDF.
  2. LLM context windows don't overflow with irrelevant pages.
  3. We can show the user "here's the exact passage that answers
     your question."

This is the *child* side of the relationship:

    Document  1 ──── * Chunk
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

# ── pgvector integration ─────────────────────────────────────────
#
# The `pgvector` Python package provides a custom SQLAlchemy column
# type called `Vector`.  It maps to Postgres's `vector(N)` type,
# which stores dense floating-point arrays for similarity search.
#
# We import it here so we can define the `embedding` column.
# If pgvector is not installed, the import would fail — but it's
# already in pyproject.toml dependencies.

from pgvector.sqlalchemy import Vector


class Chunk(Base):
    """
    Maps to the `chunks` table in Postgres.

    One Document produces many Chunks.  Each Chunk holds a slice of
    the document's text and (optionally) its vector embedding.
    """

    __tablename__ = "chunks"

    # ── Primary Key ───────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # ── Foreign Key ───────────────────────────────────────────────
    #
    # This column links each Chunk to its parent Document.
    #
    # ForeignKey("documents.id") means:
    #   "This column references the `id` column in the `documents` table."
    #
    # ondelete="CASCADE" means:
    #   "If the parent Document is DELETEd, Postgres automatically
    #    deletes all Chunks that reference it."
    #   This is a *database-level* guarantee — it works even if
    #   someone deletes via raw SQL, bypassing the ORM.

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent document this chunk belongs to.",
    )

    # ── Data Columns ─────────────────────────────────────────────

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="0-based position of this chunk within the document.",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual text content of this chunk.",
    )

    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of tokens (for billing/limit checks). Filled during chunking.",
    )

    # ── Vector Embedding ─────────────────────────────────────────
    #
    # Vector(1536) stores a 1536-dimensional float array — this is
    # the output size of OpenAI's text-embedding-ada-002 model.
    #
    # It's nullable because embeddings are computed *asynchronously*
    # after chunking.  The flow is:
    #   1. Upload → status=PENDING
    #   2. Chunking → Chunks created with content, embedding=NULL
    #   3. Embedding → embedding filled, status=READY
    #
    # We'll add an HNSW index on this column in the migration for
    # fast approximate nearest-neighbor search.

    embedding = mapped_column(
        Vector(1536),
        nullable=True,
        comment="1536-dim vector from the embedding model.",
    )

    # ── Timestamp ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────
    #
    # This is the *reverse* side of Document.chunks.
    #
    # back_populates="chunks" tells SQLAlchemy:
    #   "When you load chunk.document, the Document's .chunks list
    #    already includes this chunk — they stay in sync."
    #
    # lazy="joined" means:
    #   When you load a Chunk, SQLAlchemy does a JOIN to also load
    #   the parent Document in the *same query*.  This is efficient
    #   for many-to-one (each chunk has exactly one document).

    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"<Chunk(id={self.id!s:.8}, "
            f"document_id={self.document_id!s:.8}, "
            f"index={self.chunk_index})>"
        )


# Resolve forward reference for type checkers
from backend.app.models.document import Document  # noqa: E402, F401
