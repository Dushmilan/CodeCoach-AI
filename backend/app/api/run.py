from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.models.schemas import CodeExecutionRequest, CodeExecutionResult, Language
from app.models.auth_schemas import UserResponse
from app.ports.code_executor import CodeExecutor
from app.api.auth_deps import get_current_user
from app.api.dependencies import (
    get_executor,
    get_execution_job_repo,
)
from app.models.adapter_state_schemas import ExecutionJobListResponse
from app.ports.execution_job_repository import ExecutionJobRepository
from app.middleware.rate_limit import limiter, RUN_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=CodeExecutionResult)
@router.post("/", response_model=CodeExecutionResult)
@limiter.limit(RUN_RATE_LIMIT)
async def execute_code(
    request: Request,
    execution_request: CodeExecutionRequest,
    executor: CodeExecutor = Depends(get_executor),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Execute code using Piston API.

    Redis-only by design (Issue #264): result caching lives in
    PistonService (`exec:run`, 1h TTL). Free runs never touch Postgres —
    only /submit persists attempts. Keeps the hot path at Piston latency.
    """
    _ = request
    _ = current_user
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
        raise HTTPException(status_code=500, detail="Code execution failed")


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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Code validation failed")


@router.get("/jobs", response_model=ExecutionJobListResponse)
async def get_my_execution_jobs(
    limit: int = Query(50, ge=1, le=200, description="Max jobs to return"),
    jobs: ExecutionJobRepository = Depends(get_execution_job_repo),
    current_user: UserResponse = Depends(get_current_user),
):
    """Return the authenticated user's recent execution intents, newest first."""
    try:
        items = await jobs.list_by_user(current_user.id, limit=limit)
        return ExecutionJobListResponse(jobs=list(items), total=len(items))
    except Exception:
        logger.exception("Failed to list execution jobs for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to list execution jobs")


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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching languages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch languages")


@router.get("/runtimes")
async def get_runtimes(executor: CodeExecutor = Depends(get_executor)):
    """Get all available runtimes from Piston API."""

    try:
        runtimes = await executor.get_runtimes()
        return {"runtimes": runtimes}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching runtimes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch runtimes")
