from fastapi import APIRouter, Request
from datetime import datetime, timezone

router = APIRouter()


@router.get("/")
async def health_check(request: Request):
    rate_limiting_enabled = hasattr(request.app.state, "limiter")
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "features": {
            "ai_coaching": "enabled",
            "code_execution": "enabled",
            "questions_api": "enabled",
            "rate_limiting": "enabled" if rate_limiting_enabled else "disabled",
        },
        "dependencies": {
            "nvidia_nim": "configured",
            "piston_api": "configured",
            "questions_db": "loaded",
        },
    }
