"""
Application-wide enumerations.

Enums live in their own module (not inside a model file) so that:
  - Multiple models can import them without circular dependencies.
  - Pydantic schemas can reuse them for request/response validation.
  - They're easy to find when the project grows.
"""

from __future__ import annotations

import enum


class ProcessingStatus(str, enum.Enum):
    """
    Tracks a document's progress through the ingestion pipeline.

    The lifecycle is:

        PENDING  →  CHUNKING  →  EMBEDDING  →  READY
            ↘          ↘            ↘
            FAILED     FAILED      FAILED

    Why inherit from `str`?
    -----------------------
    By making this a (str, Enum), each member's value is a plain string.
    This means:

      1. SQLAlchemy stores it as a VARCHAR, not a Postgres ENUM type.
         VARCHAR is easier to migrate (adding a new status is just a code
         change, not an ALTER TYPE ... ADD VALUE migration).

      2. Pydantic serialises it to JSON automatically:
         {"status": "pending"}  instead of  {"status": <ProcessingStatus.PENDING>}

      3. Comparisons work naturally:
         doc.status == "pending"   →  True
         doc.status == ProcessingStatus.PENDING   →  also True
    """

    PENDING = "pending"
    """Document uploaded, waiting to be processed."""

    CHUNKING = "chunking"
    """Document is being split into chunks."""

    EMBEDDING = "embedding"
    """Chunks are being embedded into vectors."""

    READY = "ready"
    """All chunks embedded — document is searchable."""

    FAILED = "failed"
    """Something went wrong during processing."""
