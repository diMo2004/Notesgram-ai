from __future__ import annotations

import re
import threading
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class StoredDocument:
	id: str
	filename: str
	content: str
	metadata: dict[str, object] = field(default_factory=dict)
	created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


_DOCUMENTS: list[StoredDocument] = []
_LOCK = threading.Lock()


def _tokenize(text: str) -> Counter[str]:
	tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
	return Counter(tokens)


def extract_text(file_bytes: bytes, filename: str, content_type: str | None = None) -> str:
	if filename.lower().endswith(".pdf") or content_type == "application/pdf":
		try:
			import io

			from pypdf import PdfReader

			reader = PdfReader(io.BytesIO(file_bytes))
			pages = [page.extract_text() or "" for page in reader.pages]
			text = "\n".join(page.strip() for page in pages if page.strip())
			if text:
				return text
		except Exception:
			pass

	try:
		return file_bytes.decode("utf-8")
	except UnicodeDecodeError:
		return file_bytes.decode("latin-1", errors="ignore")


def store_document(filename: str, content: str, metadata: dict[str, object] | None = None) -> StoredDocument:
	document = StoredDocument(
		id=str(uuid.uuid4()),
		filename=filename,
		content=content,
		metadata=metadata or {},
	)
	with _LOCK:
		_DOCUMENTS.append(document)
	return document


def search_documents(query: str, top_k: int) -> list[tuple[StoredDocument, float]]:
	query_tokens = _tokenize(query)
	if not query_tokens:
		return []

	with _LOCK:
		documents = list(_DOCUMENTS)

	results: list[tuple[StoredDocument, float]] = []
	for document in documents:
		document_tokens = _tokenize(document.content)
		if not document_tokens:
			continue

		intersection = sum((query_tokens & document_tokens).values())
		union = sum((query_tokens | document_tokens).values())
		score = (intersection / union) if union else 0.0
		if score > 0:
			results.append((document, score))

	results.sort(key=lambda item: item[1], reverse=True)
	return results[:top_k]
