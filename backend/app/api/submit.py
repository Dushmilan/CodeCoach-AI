from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.schemas import SubmitRequest, SubmitResponse, SubmitResult
from app.models.submission_schemas import SubmissionIn
from app.models.auth_schemas import UserResponse
from app.ports.code_executor import CodeExecutor, TestCaseResult
from app.ports.question_repository import QuestionRepository
from app.ports.submission_repository import SubmissionRepository
from app.services.review_service import ReviewService
from app.api.auth_deps import get_current_user
from app.api.dependencies import (
    get_executor,
    get_question_repo,
    get_review_service,
    get_skill_graph_service,
    get_submission_repo,
)
from app.middleware.rate_limit import limiter, RUN_RATE_LIMIT
from app.models.skill_graph_schemas import LearningEvent, LearningEventType
from app.services.skill_graph_service import SkillGraphService
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
    reviews: ReviewService = Depends(get_review_service),
    skill_service: SkillGraphService = Depends(get_skill_graph_service),
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
    persisted = None
    try:
        persisted = await submissions.add(
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

    # Mistake-memory observation (Ideas #1): failures open/refresh review
    # cards; passes promote conquered bugs into the SM-2 rotation.
    # Best-effort, same contract as the submission persist above.
    try:
        await reviews.observe_submission(
            user_id=current_user.id,
            question_id=submit_request.question_id,
            passed=passed,
            error_signature=_error_signature(results),
            now=datetime.now(timezone.utc),
        )
    except Exception:  # noqa: BLE001
        logger.warning("Failed to record mistake-memory observation", exc_info=True)

    # Skill-graph emission: keep the Personal Skill Graph in sync with
    # already-persisted submissions (DB query backfill + live writes). Uses a
    # deterministic event id ``sub:{submission.id}`` so repeated syncs and
    # this live path remain idempotent via ``event_exists``. Best-effort.
    if persisted is not None:
        try:
            event = LearningEvent(
                id=f"sub:{persisted.id}",
                user_id=current_user.id,
                event_type=LearningEventType.SUBMISSION_PASSED
                if passed
                else LearningEventType.SUBMISSION_FAILED,
                question_id=submit_request.question_id,
                metadata={"error_signature": _error_signature(results)}
                if not passed and _error_signature(results)
                else {},
                occurred_at=persisted.created_at or datetime.now(timezone.utc),
            )
            await skill_service.ingest_events([event], user_id=current_user.id)
        except Exception:  # noqa: BLE001
            logger.warning(
                "Failed to emit skill-graph event for %s",
                submit_request.question_id,
                exc_info=True,
            )

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
