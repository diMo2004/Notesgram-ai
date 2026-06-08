import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base

# Note: We are using SQLite in-memory for testing the repository layer.
# This makes tests very fast and requires no external dependencies like Docker.
# However, SQLite doesn't support Postgres-specific types like Vector or JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, String

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(Vector, "sqlite")
def compile_vector_sqlite(type_, compiler, **kw):
    # Fallback to JSON or TEXT for vector representation in SQLite
    return "JSON"

@pytest.fixture(scope="session")
def engine():
    """Create a single engine for the whole test session."""
    # Use SQLite memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=None  # NullPool equivalent for sqlite
    )
    
    # Create all tables (from our models)
    # This will use SQLite's dialects to create standard tables.
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables when done
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """
    Create a fresh database session for a test.
    We don't use nested transactions here because SQLite has limited support
    for SAVEPOINT. Instead, we just truncate or rely on isolation if needed,
    but since it's an in-memory DB and we aren't truncating between tests yet,
    tests should be isolated by not relying on hardcoded IDs.
    Ideally, we'd clear tables between tests.
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()  # rollback uncommitted changes
        session.close()
        
        # Cleanup data after each test to ensure isolation
        with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
