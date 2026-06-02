from fastapi import FastAPI
from backend.app.api.v1.health import router as health_router


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router, prefix="/api/v1", tags=["health"])


def create_app() -> FastAPI:
    app = FastAPI(title="Notesgram Backend")
    register_routes(app)
    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": "notesgram-backend", "status": "running"}
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
