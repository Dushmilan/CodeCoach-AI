from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
import os
import sys

from app.core.config import is_production


def _debug_enabled() -> bool:
    """Only expose debug endpoints outside production (request-time check).

    Fail-closed: an unset ENVIRONMENT is treated as production, so the debug
    endpoints return 404 unless ENVIRONMENT is explicitly non-production."""
    if is_production():
        raise HTTPException(status_code=404, detail="Not found")
    return True


router = APIRouter(dependencies=[Depends(_debug_enabled)])
logger = logging.getLogger(__name__)


@router.get("/groq-status")
async def check_groq_status_debug() -> Dict[str, Any]:
    """Debug endpoint to check Groq API key configuration and validity."""
    from app.services.groq_verification import check_groq_status

    return await check_groq_status()


@router.get("/environment")
async def get_environment_info() -> Dict[str, Any]:
    """Debug endpoint to show relevant environment information."""
    return {
        "environment": os.getenv("ENVIRONMENT", "production"),
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        ),
        "working_directory": os.getcwd(),
        "groq_api_key_present": bool(os.getenv("GROQ_API_KEY")),
    }
