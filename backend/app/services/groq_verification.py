"""Groq API verification helpers — used by debug + admin endpoints."""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


async def check_groq_status(
    api_key: Optional[str] = None, timeout: float = 10.0
) -> Dict[str, Any]:
    """Verify the configured Groq key by listing models.

    Returns a diagnostic dict (never raises) suitable for debug/admin output.
    """
    api_key = api_key or os.getenv("GROQ_API_KEY")
    result = {
        "api_key_present": False,
        "api_key_format_valid": False,
        "valid": False,
        "models": [],
        "model_count": 0,
        "error": None,
    }

    if not api_key:
        result["error"] = "GROQ_API_KEY environment variable not set"
        return result

    result["api_key_present"] = True
    result["api_key_format_valid"] = api_key.startswith("gsk_") and len(api_key) > 20

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{GROQ_BASE_URL}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", []) if m.get("id")]
            result["valid"] = True
            result["models"] = sorted(models)
            result["model_count"] = len(models)
        elif response.status_code == 401:
            result["error"] = "Invalid API key (401 Unauthorized)"
        else:
            result["error"] = f"Groq API returned status {response.status_code}"
    except httpx.TimeoutException:
        result["error"] = "Groq API request timed out"
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error checking Groq status: {e}")

    return result


async def list_groq_models(api_key: Optional[str] = None) -> List[str]:
    """Return available model ids for the configured key (empty on failure)."""
    status = await check_groq_status(api_key=api_key)
    return status.get("models", [])
