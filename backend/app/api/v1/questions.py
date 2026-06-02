from __future__ import annotations

from fastapi import APIRouter

from backend.app.services.retrieval import search_documents
from backend.app.validation.retrieval import QueryNeighbor, QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(payload: QueryRequest) -> QueryResponse:
	matches = search_documents(payload.query, payload.top_k)
	neighbors = [
		QueryNeighbor(
			document_id=document.id,
			filename=document.filename,
			score=score,
			excerpt=document.content[:400],
			content_length=len(document.content),
		)
		for document, score in matches
	]

	return QueryResponse(
		query=payload.query,
		top_k=payload.top_k,
		nearest_neighbors=neighbors,
	)
