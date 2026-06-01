from fastapi import FastAPI
from backend.app.api.v1.health import router as health_router

app = FastAPI(title="Notesgram Backend")
app.include_router(health_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"service": "notesgram-backend", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
