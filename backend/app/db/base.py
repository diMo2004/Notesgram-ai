"""
Declarative base for all SQLAlchemy ORM models.

Every model in app/models/ inherits from `Base`. This gives us:
  1. A shared `metadata` object — the single source of truth for all table
     definitions. Alembic reads this to auto-generate migrations.
  2. A consistent place to define conventions (like naming patterns for
     constraints) that apply to every table automatically.

Usage:
    from backend.app.db.base import Base

    class MyModel(Base):
        __tablename__ = "my_table"
        ...
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    Why DeclarativeBase instead of declarative_base()?
    --------------------------------------------------
    SQLAlchemy 2.0 introduced DeclarativeBase as a class-based replacement
    for the older declarative_base() function. It plays better with type
    checkers (mypy, Pyright) because your models become proper subclasses
    with discoverable attributes.

    The old way:  Base = declarative_base()       # returns Any, hard to type
    The new way:  class Base(DeclarativeBase): ... # fully typed, IDE-friendly
    """

    pass
