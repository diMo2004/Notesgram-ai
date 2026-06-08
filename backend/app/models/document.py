"""
Document ORM model.

A Document represents a single uploaded file (e.g., a PDF, text file).
It is the *parent* side of the one-to-many relationship:

    Document  1 ──── * Chunk

Key design decisions documented inline below.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.enums import ProcessingStatus


class Document(Base):
    """
    Maps to the `documents` table in Postgres.

    __tablename__
    ─────────────
    This string is the actual SQL table name.  SQLAlchemy uses it to
    generate CREATE TABLE, SELECT, INSERT, etc.  Always use plural
    snake_case by convention.
    """

    __tablename__ = "documents"

    # ── Primary Key ───────────────────────────────────────────────────
    #
    # We use UUIDs instead of auto-incrementing integers because:
    #   1. They're globally unique — safe to merge data across databases.
    #   2. They don't reveal how many records exist (sequential IDs do).
    #   3. They can be generated client-side before the INSERT.
    #
    # `server_default=func.gen_random_uuid()` tells Postgres to generate
    # the UUID if Python doesn't provide one.  This is a Postgres-side
    # default, NOT a Python-side default.
    #
    # Mapped[uuid.UUID] is the new SQLAlchemy 2.0 type annotation style.
    # It tells both SQLAlchemy and your IDE/type-checker what type this
    # column holds.

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # ── Data Columns ──────────────────────────────────────────────────

    filename: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Original filename as uploaded by the user.",
    )

    content_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="application/octet-stream",
        comment="MIME type, e.g. application/pdf, text/plain.",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ProcessingStatus.PENDING.value,
        server_default=ProcessingStatus.PENDING.value,
        comment="Current pipeline stage. See ProcessingStatus enum.",
    )

    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of pages (for PDFs). Filled after parsing.",
    )

    # ── JSONB metadata ────────────────────────────────────────────────
    #
    # JSONB is Postgres-specific.  It stores arbitrary JSON and supports
    # indexing/querying into the JSON structure.  We use it for flexible
    # metadata that doesn't deserve its own column (e.g., author, tags).
    #
    # The column is named `metadata_` (trailing underscore) because
    # `metadata` conflicts with SQLAlchemy's Base.metadata attribute.

    metadata_: Mapped[dict] = mapped_column(
        "metadata",  # ← actual SQL column name is "metadata" (no underscore)
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Arbitrary extra data (tags, author, source URL, etc.).",
    )

    # ── Timestamps ────────────────────────────────────────────────────
    #
    # server_default=func.now() tells Postgres to set the timestamp
    # on INSERT.  This is better than a Python-side default because:
    #   - It uses the DB server's clock (consistent in distributed setups).
    #   - It works even if someone inserts via raw SQL or another app.
    #
    # onupdate=func.now() tells SQLAlchemy to set updated_at whenever
    # the ORM issues an UPDATE.  (For raw SQL updates, the DB trigger
    # from the old migration would handle it — but we rely on ORM here.)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────────
    #
    # `relationship("Chunk")` tells SQLAlchemy:
    #   "A Document has many Chunks.  You can access them via doc.chunks."
    #
    # back_populates="document" creates the reverse link:
    #   chunk.document → the parent Document object.
    #
    # cascade="all, delete-orphan":
    #   - "all"           → propagate add/merge/refresh/expunge to children.
    #   - "delete-orphan" → if you remove a Chunk from doc.chunks, that
    #                        Chunk gets DELETEd from the DB automatically.
    #   Combined with the FK ON DELETE CASCADE, deleting a Document
    #   also deletes all its Chunks.
    #
    # lazy="selectin":
    #   When you load a Document, SQLAlchemy issues a second SELECT
    #   to batch-load all related Chunks.  This avoids the "N+1 query"
    #   problem where accessing doc.chunks in a loop would fire one
    #   query per document.  "selectin" is the best general-purpose
    #   strategy for one-to-many.
    #
    # order_by="Chunk.chunk_index":
    #   Chunks come back sorted by their position within the document.

    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Chunk.chunk_index",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id!s:.8}, filename={self.filename!r}, status={self.status})>"


# Avoid circular import — Chunk is only needed for the type annotation
# in `relationship()`.  The string "Chunk" works because SQLAlchemy
# resolves it lazily from the Base registry.
from backend.app.models.chunk import Chunk  # noqa: E402, F401
