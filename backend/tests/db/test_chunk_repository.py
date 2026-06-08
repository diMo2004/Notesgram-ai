import pytest

from backend.app.db.repositories.chunk_repository import ChunkRepository
from backend.app.db.repositories.document_repository import DocumentRepository

def test_bulk_create_and_get_chunks(db_session):
    doc_repo = DocumentRepository(db_session)
    chunk_repo = ChunkRepository(db_session)
    
    doc = doc_repo.create(filename="big.pdf")
    db_session.commit()
    
    chunks_data = [
        {"chunk_index": 0, "content": "First part"},
        {"chunk_index": 1, "content": "Second part"},
        {"chunk_index": 2, "content": "Third part"}
    ]
    
    chunks = chunk_repo.bulk_create(doc.id, chunks_data)
    db_session.commit()
    
    assert len(chunks) == 3
    assert chunks[0].content == "First part"
    
    # Test getting by document correctly sorted
    retrieved = chunk_repo.get_by_document(doc.id)
    assert len(retrieved) == 3
    assert retrieved[0].chunk_index == 0
    assert retrieved[2].chunk_index == 2

def test_cascade_delete(db_session):
    doc_repo = DocumentRepository(db_session)
    chunk_repo = ChunkRepository(db_session)
    
    doc = doc_repo.create(filename="cascade.pdf")
    db_session.commit()
    
    chunk_repo.bulk_create(doc.id, [
        {"chunk_index": 0, "content": "Only part"}
    ])
    db_session.commit()
    
    # Verify chunk exists
    chunks_before = chunk_repo.get_by_document(doc.id)
    assert len(chunks_before) == 1
    chunk_id = chunks_before[0].id
    
    # Delete doc
    doc_repo.delete(doc.id)
    db_session.commit()
    
    # Verify chunk is gone (Cascade)
    assert chunk_repo.get_by_id(chunk_id) is None
