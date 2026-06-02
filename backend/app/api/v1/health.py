from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    database_url = getattr(getattr(request.app.state, "database", None), "database_url", None)
    return {
        "status": "ok",
        "database_configured": bool(database_url),
    }
