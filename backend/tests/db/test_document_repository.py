import pytest
from uuid import uuid4

from backend.app.db.repositories.document_repository import DocumentRepository
from backend.app.models.enums import ProcessingStatus
from backend.app.models.document import Document

def test_create_document(db_session):
    repo = DocumentRepository(db_session)
    
    doc = repo.create(
        filename="test.pdf",
        content_type="application/pdf"
    )
    db_session.commit()
    
    assert doc.id is not None
    assert doc.filename == "test.pdf"
    # Should default to pending
    assert doc.status == ProcessingStatus.PENDING.value
    assert doc.created_at is not None

def test_get_by_id(db_session):
    repo = DocumentRepository(db_session)
    
    doc = repo.create(filename="find_me.pdf")
    db_session.commit()
    
    found = repo.get_by_id(doc.id)
    assert found is not None
    assert found.filename == "find_me.pdf"
    
    not_found = repo.get_by_id(uuid4())
    assert not_found is None

def test_update_status(db_session):
    repo = DocumentRepository(db_session)
    
    doc = repo.create(filename="status.pdf")
    db_session.commit()
    
    updated = repo.update_status(doc.id, ProcessingStatus.CHUNKING)
    db_session.commit()
    
    assert updated is not None
    assert updated.status == ProcessingStatus.CHUNKING.value
    
    # Refetch to ensure it's saved
    refetched = repo.get_by_id(doc.id)
    assert refetched is not None
    assert refetched.status == ProcessingStatus.CHUNKING.value

def test_get_by_status(db_session):
    repo = DocumentRepository(db_session)
    
    doc1 = repo.create(filename="doc1.pdf", status=ProcessingStatus.PENDING.value)
    doc2 = repo.create(filename="doc2.pdf", status=ProcessingStatus.READY.value)
    db_session.commit()
    
    pending_docs = repo.get_by_status(ProcessingStatus.PENDING)
    assert len(pending_docs) == 1
    assert pending_docs[0].id == doc1.id

def test_delete_document(db_session):
    repo = DocumentRepository(db_session)
    
    doc = repo.create(filename="delete_me.pdf")
    db_session.commit()
    
    assert repo.delete(doc.id) is True
    db_session.commit()
    
    assert repo.get_by_id(doc.id) is None
    assert repo.delete(uuid4()) is False
