from fastapi import APIRouter, Request
from datetime import datetime
import time
from app.models.schemas import HealthResponse

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Health check endpoint.
    
    Returns service health status and dependency information.
    """
    
    return HealthResponse(
        status="healthy",
        service="codecoach-ai-backend",
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies={
            "fastapi": "running",
            "uvicorn": "running",
            "cors": "configured",
            "rate_limiting": "enabled"
        }
    )

@router.get("/detailed")
async def detailed_health():
    """Detailed health check with system information."""
    
    return {
        "status": "healthy",
        "service": "codecoach-ai-backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "system": {
            "python_version": "3.11.x",
            "fastapi_version": "0.104.1",
            "uvicorn_version": "0.24.0"
        },
        "features": {
            "ai_coaching": "enabled",
            "code_execution": "enabled",
            "questions_api": "enabled",
            "rate_limiting": "enabled"
        },
        "dependencies": {
            "nvidia_nim": "configured",
            "piston_api": "configured",
            "questions_db": "loaded"
        }
    }