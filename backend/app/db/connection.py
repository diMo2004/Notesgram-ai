"""
Database engine, session factory, and FastAPI dependency.

Three key concepts:
━━━━━━━━━━━━━━━━━━

1. ENGINE  — The connection pool. Think of it as the "phone line" to
   Postgres. You create ONE engine for the entire app and reuse it.
   It manages a pool of actual TCP connections behind the scenes.

2. SESSION FACTORY (sessionmaker) — A factory that stamps out Session
   objects. Each Session is an independent "unit of work" — it tracks
   which objects you've read, created, or modified, and flushes them
   to the database when you commit.

   Why a factory?  Because each web request needs its own Session.
   If two requests shared the same Session, one request's uncommitted
   changes would leak into the other.  That's a data-corruption bug.

3. get_db() — A FastAPI dependency (generator) that:
   - Opens a new Session at the start of a request.
   - Yields it to the route handler.
   - Guarantees cleanup (close) when the request finishes, even if
     the handler threw an exception.

Flow:
    Request arrives
        → FastAPI calls get_db()
        → Session opens
        → Your route handler runs, using the Session
        → Handler returns (or crashes)
        → get_db()'s `finally` block closes the Session
    Response sent
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings

# ─── 1. ENGINE ────────────────────────────────────────────────────────
#
# create_engine() doesn't open a connection right away — it just
# configures the pool.  Actual connections are created lazily when
# the first query runs.
#
# echo=False in production.  Set to True temporarily if you want to
# see every SQL statement SQLAlchemy generates (very helpful for
# learning, noisy in prod).
#
# pool_pre_ping=True makes SQLAlchemy send a lightweight "SELECT 1"
# before reusing a pooled connection, to detect stale / dropped
# connections (e.g., after Postgres restarts).

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

# ─── 2. SESSION FACTORY ──────────────────────────────────────────────
#
# sessionmaker returns a *class* (not an instance).  Calling
# SessionLocal() later will create a fresh Session bound to our engine.
#
# autocommit=False  → You must explicitly call db.commit().
#                     This is the safe default: nothing is written
#                     until you say so.
# autoflush=False   → SQLAlchemy won't auto-flush pending changes
#                     before every query.  This gives you full control
#                     over when writes happen.
# expire_on_commit=False → After commit(), objects stay usable without
#                          hitting the DB again.  Without this, accessing
#                          any attribute after commit triggers a lazy load.

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ─── 3. FASTAPI DEPENDENCY ───────────────────────────────────────────
#
# This is a Python generator used as a FastAPI "Depends(...)".
#
# Example usage in a route:
#
#   @router.post("/documents")
#   def create_document(db: Session = Depends(get_db)):
#       doc = Document(filename="notes.pdf")
#       db.add(doc)
#       db.commit()
#       return doc
#
# The `finally` block is the key safety net — it ensures the session
# is closed whether the handler succeeds or raises an exception.

def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()