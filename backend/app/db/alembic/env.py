"""
Alembic migration environment.

This file is the "brain" of Alembic.  It runs every time you execute
an Alembic command (upgrade, downgrade, revision, etc.).

Its job is:
  1. Connect to the database.
  2. Tell Alembic about your ORM models (via Base.metadata).
  3. Run migrations inside a proper transaction.

HOW AUTOGENERATE WORKS
──────────────────────
When you run `alembic revision --autogenerate`, Alembic:

  1. Reads Base.metadata  →  "Here's what the models SAY the schema should be"
  2. Connects to the DB   →  "Here's what the schema ACTUALLY is right now"
  3. Computes the diff    →  "You need to ADD column X, CREATE table Y, etc."
  4. Writes a migration   →  A Python script with upgrade() and downgrade()

This is why the model imports below are CRITICAL.  If a model isn't
imported, it won't be registered on Base.metadata, and Alembic won't
know it exists.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Ensure 'backend' package is importable ────────────────────────
#
# When Alembic loads this file, Python's working directory is
# `backend/`, but `backend` itself isn't a proper installed package
# (it uses namespace packages).  We need the *parent* of `backend/`
# on sys.path so that `from backend.app.db.base import Base` works.
#
# This is the same trick used in tests/conftest.py.

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[4]  # alembic/env.py → db → app → backend → project root
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ── Import Base and ALL models ────────────────────────────────────
#
# Base.metadata is the object Alembic inspects.  But metadata is only
# populated when model classes are *imported* (because the class body
# executes `mapped_column(...)`, which registers columns on metadata).
#
# So we MUST import every model here, even if we don't "use" them
# directly.  The noqa comments tell linters "yes, this import has
# side effects — that's intentional."

from backend.app.db.base import Base  # noqa: F401
from backend.app.models.document import Document  # noqa: F401
from backend.app.models.chunk import Chunk  # noqa: F401

# ── Alembic Config object ────────────────────────────────────────
# This gives access to values in alembic.ini via config.get_main_option()
config = context.config

# ── Set up logging from alembic.ini ──────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata for autogenerate ─────────────────────────────
# This is THE key line.  Alembic uses this metadata to compare
# "what models say" vs "what the database has."
target_metadata = Base.metadata

# ── Override the database URL ────────────────────────────────────
#
# We read DATABASE_URL from the environment so that:
#   1. Secrets don't live in alembic.ini (which is committed to git).
#   2. Different environments (dev, staging, prod) just set a different
#      env var — no config file changes needed.

import os

database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This generates SQL scripts WITHOUT connecting to the database.
    Useful for:
      - Generating SQL to hand to a DBA for review.
      - Environments where you can't connect directly.

    Usage: `alembic upgrade head --sql`
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    This connects to the database, runs the migrations inside a
    transaction, and commits.  This is what happens when you run:

        alembic upgrade head

    The transaction ensures that if a migration fails halfway through,
    all changes are rolled back — your database is never left in a
    half-migrated state.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Don't pool — migrations are one-shot
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ── Entry point ──────────────────────────────────────────────────
# Alembic calls either offline or online depending on context.

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
