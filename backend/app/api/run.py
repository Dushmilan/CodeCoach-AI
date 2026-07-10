from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import CodeExecutionRequest, CodeExecutionResult, Language
from app.ports.code_executor import CodeExecutor
from app.api.auth import get_current_user
from app.api.dependencies import get_executor
from app.middleware.rate_limit import limiter, RUN_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/", response_model=CodeExecutionResult)
@limiter.limit(RUN_RATE_LIMIT)
async def execute_code(
    request: Request,
    execution_request: CodeExecutionRequest,
    executor: CodeExecutor = Depends(get_executor),
):
    """
    Execute code using Piston API.

    Supports multiple programming languages with safe execution environment.
    """
    try:
        result = await executor.execute(
            language=execution_request.language.value,
            code=execution_request.code,
            stdin=execution_request.stdin,
            version=execution_request.version,
        )

        return CodeExecutionResult(**asdict(result))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error executing code: {str(e)}")


@router.post("/validate")
@limiter.limit(RUN_RATE_LIMIT)
async def validate_code(
    request: Request,
    execution_request: CodeExecutionRequest,
    executor: CodeExecutor = Depends(get_executor),
):
    """
    Validate code before execution.

    Provides syntax checking and basic validation without full execution.
    """

    try:
        validation = executor.validate_code(
            language=execution_request.language.value, code=execution_request.code
        )

        return {
            "valid": validation["valid"],
            "warnings": validation["warnings"],
            "errors": validation["errors"],
            "language": execution_request.language.value,
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
