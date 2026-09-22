from datetime import datetime, timezone

import asyncio

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
    get_redis_cache,
    get_review_service,
    get_skill_graph_service_dependency,
    get_submission_repo,
)
from app.middleware.rate_limit import limiter, RUN_RATE_LIMIT
from app.models.skill_graph_schemas import LearningEvent, LearningEventType
from app.services.learner_context_service import LearnerContextService
from app.services.redis_service import RedisCache
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


async def _invalidate_learner_cache(user_id: str, cache: RedisCache | None) -> None:
    if not cache or not user_id:
        return
    try:
        svc = LearnerContextService(
            cache=cache, skill_service=None, submission_repo=None
        )
        await svc.invalidate(user_id)
    except Exception:  # pragma: no cover
        pass


async def _record_post_grading(
    reviews: ReviewService,
    skill_service: SkillGraphService | None,
    cache: RedisCache | None,
    user_id: str,
    question_id: str,
    passed: bool,
    error_signature: str | None,
    persisted,
    now: datetime,
) -> None:
    """Record grading side effects concurrently (#264).

    Mistake-memory observation, skill-graph emission, and learner-cache
    invalidation are independent best-effort writes — they overlap instead
    of adding up. Failures degrade to warnings, never to a 500.
    """

    async def _observe():
        try:
            await reviews.observe_submission(
                user_id=user_id,
                question_id=question_id,
                passed=passed,
                error_signature=error_signature,
                now=now,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Failed to record mistake-memory observation", exc_info=True)

    async def _skill():
        if persisted is None or skill_service is None:
            return
        try:
            event = LearningEvent(
                id=f"sub:{persisted.id}",
                user_id=user_id,
                event_type=LearningEventType.SUBMISSION_PASSED
                if passed
                else LearningEventType.SUBMISSION_FAILED,
                question_id=question_id,
                metadata={"error_signature": error_signature}
                if not passed and error_signature
                else {},
                occurred_at=persisted.created_at or now,
            )
            await skill_service.ingest_events([event], user_id=user_id)
        except Exception:  # noqa: BLE001
            logger.warning(
                "Failed to emit skill-graph event for %s",
                question_id,
                exc_info=True,
            )

    async def _invalidate():
        try:
            await _invalidate_learner_cache(user_id, cache)
        except Exception:
            pass

    await asyncio.gather(_observe(), _skill(), _invalidate())


@router.post("", response_model=SubmitResponse)
@router.post("/", response_model=SubmitResponse)
@limiter.limit(RUN_RATE_LIMIT)
async def submit_code(
    request: Request,
    submit_request: SubmitRequest,
    repository: QuestionRepository = Depends(get_question_repo),
    executor: CodeExecutor = Depends(get_executor),
    submissions: SubmissionRepository = Depends(get_submission_repo),
    reviews: ReviewService = Depends(get_review_service),
    skill_service: SkillGraphService = Depends(get_skill_graph_service_dependency),
    cache: RedisCache | None = Depends(get_redis_cache),
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

    # Learn-surface practice grades without persisting anything:
    # no submission rows, no mistake-memory observation, no skill events,
    # no learner-cache invalidation (curriculum runs must not pollute the
    # moat).
    is_learn = submit_request.surface == "learn"

    # Stateful adapter contract: persist sent before grading so executor
    # crashes still leave an auditable row, then transition to graded/failed.
    # Persistence is best-effort and never breaks the graded response.
    sent = None
    if not is_learn:
        try:
            sent = await submissions.create_sent(
                user_id=current_user.id,
                submission=SubmissionIn(
                    question_id=submit_request.question_id,
                    code=submit_request.code,
                    language=submit_request.language.value,
                    passed=False,
                ),
            )
        except Exception:  # noqa: BLE001
            logger.warning("Failed to persist submission sent state", exc_info=True)
            sent = None

    try:
        results = await executor.evaluate_suite(
            language=submit_request.language.value,
            code=submit_request.code,
            test_cases=test_cases,
        )
    except HTTPException:
        if sent is not None:
            try:
                await submissions.mark_failed(sent.id)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Failed to persist submission failed state", exc_info=True
                )
        raise
    except Exception as e:
        logger.error(f"Submit evaluation error: {e}", exc_info=True)
        if sent is not None:
            try:
                await submissions.mark_failed(sent.id)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Failed to persist submission failed state", exc_info=True
                )
        raise HTTPException(status_code=500, detail="Evaluation failed")

    passed_count = sum(1 for r in results if r.passed)
    passed = passed_count == len(results) if results else False

    # Transition sent -> graded for the mistake-memory data layer.
    # Best-effort: a failed write must not 500 the graded result.
    # Skipped entirely on the learn surface (no learn submit data persists).
    persisted = None
    if not is_learn:
        try:
            if sent is not None:
                persisted = await submissions.mark_graded(
                    sent.id,
                    passed=passed,
                    error_signature=_error_signature(results),
                )
            else:
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

    # Learn-surface side effects are skipped entirely below: nothing was
    # written, so there is no mistake-memory to observe, no skill event to
    # emit, and cached problem context stays valid (avoids a needless refill).
    if not is_learn:
        now = datetime.now(timezone.utc)
        await _record_post_grading(
            reviews=reviews,
            skill_service=skill_service,
            cache=cache,
            user_id=current_user.id,
            question_id=submit_request.question_id,
            passed=passed,
            error_signature=_error_signature(results),
            persisted=persisted,
            now=now,
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
