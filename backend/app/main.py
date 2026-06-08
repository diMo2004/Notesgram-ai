from fastapi import FastAPI

from backend.app.core.config import get_settings
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.questions import router as questions_router
from backend.app.api.v1.uploads import router as uploads_router
from backend.app.db.connection import engine


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(uploads_router, prefix="/api/v1", tags=["documents"])
    app.include_router(questions_router, prefix="/api/v1", tags=["questions"])


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Notesgram Backend")
    app.state.settings = settings
    app.state.engine = engine
    # Keep backward compat for health endpoint: it checks .database.database_url
    app.state.database = type("_DB", (), {"database_url": str(settings.database_url)})()
    register_routes(app)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": "notesgram-backend", "status": "running"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
