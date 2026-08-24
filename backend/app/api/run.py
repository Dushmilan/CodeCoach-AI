from dataclasses import asdict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import CodeExecutionRequest, CodeExecutionResult, Language
from app.models.auth_schemas import UserResponse
from app.models.submission_schemas import SubmissionIn
from app.ports.code_executor import CodeExecutor
from app.api.auth_deps import get_current_user
from app.api.dependencies import get_executor, get_review_service, get_submission_repo
from app.ports.submission_repository import SubmissionRepository
from app.services.review_service import ReviewService
from app.middleware.rate_limit import limiter, RUN_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


def _crash_signature(stderr: str) -> str | None:
    """Derive a mistake-memory signature from a crashed run's stderr.

    The first non-empty line, whitespace-stripped and capped at 255 chars,
    keeps cardinality manageable while staying human-recognisable.
    """
    for line in stderr.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:255]
    return None


@router.post("/", response_model=CodeExecutionResult)
@limiter.limit(RUN_RATE_LIMIT)
async def execute_code(
    request: Request,
    execution_request: CodeExecutionRequest,
    executor: CodeExecutor = Depends(get_executor),
    submissions: SubmissionRepository = Depends(get_submission_repo),
    reviews: ReviewService = Depends(get_review_service),
    current_user: UserResponse = Depends(get_current_user),
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

        # Mistake-memory capture (Ideas #1): a crashed free-run inside a
        # question workspace is an attempt. Best-effort, mirroring submit.py.
        if (
            execution_request.question_id
            and result.exit_code != 0
            and current_user is not None
        ):
            try:
                signature = _crash_signature(result.stderr or "")
                await submissions.add(
                    user_id=current_user.id,
                    submission=SubmissionIn(
                        question_id=execution_request.question_id,
                        code=execution_request.code,
                        language=execution_request.language.value,
                        passed=False,
                        error_signature=signature,
                    ),
                )
                await reviews.observe_submission(
                    user_id=current_user.id,
                    question_id=execution_request.question_id,
                    passed=False,
                    error_signature=signature,
                    now=datetime.now(timezone.utc),
                )
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Failed to record crashed run for question %s",
                    execution_request.question_id,
                    exc_info=True,
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
