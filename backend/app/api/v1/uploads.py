from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.services.retrieval import extract_text, store_document
from backend.app.validation.retrieval import IngestDocumentResponse

router = APIRouter()


@router.post("/docs", response_model=IngestDocumentResponse, status_code=201)
async def ingest_document(
	file: UploadFile = File(...),
	source: str | None = Form(default=None),
) -> IngestDocumentResponse:
	file_bytes = await file.read()
	if not file_bytes:
		raise HTTPException(status_code=400, detail="Uploaded file is empty")

	content = extract_text(file_bytes, filename=file.filename or "uploaded-file", content_type=file.content_type)
	if not content.strip():
		raise HTTPException(status_code=400, detail="Could not extract text from the uploaded document")

	metadata: dict[str, object] = {}
	if source:
		metadata["source"] = source
	if file.content_type:
		metadata["content_type"] = file.content_type

	document = store_document(
		filename=file.filename or "uploaded-file",
		content=content,
		metadata=metadata,
	)

	return IngestDocumentResponse(
		document_id=document.id,
		filename=document.filename,
		status="COMPLETED",
		content_length=len(content),
	)
