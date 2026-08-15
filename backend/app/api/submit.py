from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.schemas import SubmitRequest, SubmitResponse, SubmitResult
from app.models.submission_schemas import SubmissionIn
from app.models.auth_schemas import UserResponse
from app.ports.code_executor import CodeExecutor, TestCaseResult
from app.ports.question_repository import QuestionRepository
from app.ports.submission_repository import SubmissionRepository
from app.api.auth_deps import get_current_user
from app.api.dependencies import (
    get_executor,
    get_question_repo,
    get_submission_repo,
)
from app.middleware.rate_limit import limiter, RUN_RATE_LIMIT
import logging

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])


def _error_signature(results: list[TestCaseResult]) -> str | None:
    """Derive a compact, stable error signature from the first failing case."""
    for r in results:
        if not r.passed:
            snippet = f"expected {r.expected!r}, got {r.actual!r}"
            return snippet[:255]
    return None


@router.post("/", response_model=SubmitResponse)
@limiter.limit(RUN_RATE_LIMIT)
async def submit_code(
    request: Request,
    submit_request: SubmitRequest,
    repository: QuestionRepository = Depends(get_question_repo),
    executor: CodeExecutor = Depends(get_executor),
    submissions: SubmissionRepository = Depends(get_submission_repo),
    current_user: UserResponse = Depends(get_current_user),
):
    question = await repository.get_by_id(submit_request.question_id)
    if not question:
        raise HTTPException(
            status_code=404, detail=f"Question not found: {submit_request.question_id}"
        )

    test_cases = [
        {
            "input": tc.input,
            "expected_output": tc.expected_output,
            "hidden": tc.hidden,
        }
        for tc in question.test_cases
    ]

    try:
        results = await executor.evaluate_suite(
            language=submit_request.language.value,
            code=submit_request.code,
            test_cases=test_cases,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Evaluation failed")

    passed_count = sum(1 for r in results if r.passed)
    passed = passed_count == len(results) if results else False

    # Persist the graded attempt for the mistake-memory data layer. Best-effort:
    # a failed write must not 500 the graded result, but it IS logged.
    try:
        await submissions.add(
            user_id=current_user.id,
            submission=SubmissionIn(
                question_id=submit_request.question_id,
                code=submit_request.code,
                language=submit_request.language.value,
                passed=passed,
                error_signature=_error_signature(results),
            ),
        )
    except Exception:  # noqa: BLE001
        logger.warning("Failed to persist submission", exc_info=True)

    return SubmitResponse(
        passed=passed,
        total=len(results),
        passed_count=passed_count,
        results=[
            SubmitResult(
                index=r.index,
                passed=r.passed,
                input=r.input,
                expected=r.expected,
                actual=r.actual,
                hidden=r.hidden,
            )
            for r in results
        ],
    )
