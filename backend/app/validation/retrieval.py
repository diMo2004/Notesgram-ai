from __future__ import annotations

from pydantic import BaseModel, Field


class IngestDocumentResponse(BaseModel):
	document_id: str
	filename: str
	status: str
	content_length: int


class QueryRequest(BaseModel):
	query: str = Field(min_length=1, max_length=10_000)
	top_k: int = Field(default=5, ge=1, le=20)


class QueryNeighbor(BaseModel):
	document_id: str
	filename: str
	score: float
	excerpt: str
	content_length: int


class QueryResponse(BaseModel):
	query: str
	top_k: int
	nearest_neighbors: list[QueryNeighbor]
