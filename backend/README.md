Notesgram Backend

Quick start:
1. Install dependencies: `pip install -r requirements.txt` or use the `pyproject.toml` with your preferred tool.
2. Run: `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`
3. Health: `GET /api/v1/health`
