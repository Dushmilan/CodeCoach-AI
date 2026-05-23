from fastapi import APIRouter, Depends, HTTPException
from functools import lru_cache
from app.models.schemas import CodeExecutionRequest, CodeExecutionResult, Language
from app.services.piston_service import PistonService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache()
def get_piston_service() -> PistonService:
    """Get or create Piston service instance (cached)."""
    return PistonService()


@router.post("/", response_model=CodeExecutionResult)
async def execute_code(
    request: CodeExecutionRequest,
    piston_service: PistonService = Depends(get_piston_service),
):
    """
    Execute code using Piston API.

    Supports multiple programming languages with safe execution environment.
    """

    try:
        result = await piston_service.execute_code(
            language=request.language.value,
            code=request.code,
            stdin=request.stdin,
            version=request.version,
        )

        logger.info(f"Raw result from piston_service: {result}")

        return CodeExecutionResult(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error executing code: {str(e)}")


@router.post("/validate")
async def validate_code(
    request: CodeExecutionRequest,
    piston_service: PistonService = Depends(get_piston_service),
):
    """
    Validate code before execution.

    Provides syntax checking and basic validation without full execution.
    """

    try:
        validation = piston_service.validate_code(
            language=request.language.value, code=request.code
        )

        return {
            "valid": validation["valid"],
            "warnings": validation["warnings"],
            "errors": validation["errors"],
            "language": request.language.value,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating code: {str(e)}")


@router.get("/languages")
async def get_supported_languages(
    piston_service: PistonService = Depends(get_piston_service),
):
    """Get supported programming languages and their versions."""

    try:
        runtimes = await piston_service.get_runtimes()

        # Filter and format the runtimes
        supported_languages = []
        for runtime in runtimes:
            language = runtime.get("language", "")
            if language in [lang.value for lang in Language]:
                supported_languages.append(
                    {
                        "language": language,
                        "version": runtime.get("version", ""),
                        "aliases": runtime.get("aliases", []),
                        "runtime": runtime.get("runtime", ""),
                    }
                )

        return {"languages": supported_languages, "total": len(supported_languages)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching languages: {str(e)}"
        )


@router.get("/runtimes")
async def get_runtimes(piston_service: PistonService = Depends(get_piston_service)):
    """Get all available runtimes from Piston API."""

    try:
        runtimes = await piston_service.get_runtimes()
        return {"runtimes": runtimes}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching runtimes: {str(e)}"
        )
