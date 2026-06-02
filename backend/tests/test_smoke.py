from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_reports_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database_configured"] is True