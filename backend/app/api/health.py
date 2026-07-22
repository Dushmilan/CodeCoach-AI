from fastapi import APIRouter, Request
from datetime import datetime, timezone
from importlib.metadata import version

router = APIRouter()


@router.get("/")
async def health_check(request: Request):
    rate_limiting_enabled = hasattr(request.app.state, "limiter")
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "system": {
            "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
            "fastapi_version": version("fastapi"),
            "uvicorn_version": version("uvicorn"),
        },
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
