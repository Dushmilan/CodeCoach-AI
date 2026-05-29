from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException
from functools import lru_cache

from app.models.schemas import CodeExecutionRequest, CodeExecutionResult, Language
from app.ports.code_executor import CodeExecutor
from app.services.piston_service import PistonService
from app.api.auth import get_current_user
from app.models.auth_schemas import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


@lru_cache()
def get_executor() -> CodeExecutor:
    """Get or create Piston service instance (cached)."""
    return PistonService()


@router.post("/", response_model=CodeExecutionResult)
async def execute_code(
    request: CodeExecutionRequest,
    executor: CodeExecutor = Depends(get_executor),
):
    """
    Execute code using Piston API.

    Supports multiple programming languages with safe execution environment.
    """
    try:
        result = await executor.execute(
            language=request.language.value,
            code=request.code,
            stdin=request.stdin,
            version=request.version,
        )

        return CodeExecutionResult(**asdict(result))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error executing code: {str(e)}")


@router.post("/validate")
async def validate_code(
    request: CodeExecutionRequest,
    executor: CodeExecutor = Depends(get_executor),
):
    """
    Validate code before execution.

    Provides syntax checking and basic validation without full execution.
    """

    try:
        validation = executor.validate_code(
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
    executor: CodeExecutor = Depends(get_executor),
):
    """Get supported programming languages and their versions."""

    try:
        runtimes = await executor.get_runtimes()

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
async def get_runtimes(executor: CodeExecutor = Depends(get_executor)):
    """Get all available runtimes from Piston API."""

    try:
        runtimes = await executor.get_runtimes()
        return {"runtimes": runtimes}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching runtimes: {str(e)}"
        )
