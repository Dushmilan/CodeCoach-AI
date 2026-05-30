from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",

        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "system": {
            "python_version": "3.11.x",
            "fastapi_version": "0.104.1",
            "uvicorn_version": "0.24.0",
        },
        "features": {
            "ai_coaching": "enabled",
            "code_execution": "enabled",
            "questions_api": "enabled",
            "rate_limiting": "enabled",
        },
        "dependencies": {
            "nvidia_nim": "configured",
            "piston_api": "configured",
            "questions_db": "loaded",
        },
    }
