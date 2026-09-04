"""Submit grading with durable sent/submitted/failed state.

Thin orchestration over the submission repository and a code executor:
persist sent before grading so executor crashes still leave an auditable
row, then transition to graded/failed. Follows the layered architecture:
API -> service -> repository ports -> SQL implementations.
"""

import logging
from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission_schemas import Submission, SubmissionIn
from app.repositories.sql_submission_repository import SqlSubmissionRepository

logger = logging.getLogger(__name__)


def _error_signature(results: Sequence[Any]) -> Optional[str]:
    for r in results:
        passed = getattr(r, "passed", False)
        if not passed:
            expected = getattr(r, "expected", "")
            actual = getattr(r, "actual", "")
            return f"expected {expected!r}, got {actual!r}"[:255]
    return None


async def grade_submission_with_state(
    *,
    db: AsyncSession,
    executor: Any,
    user_id: str,
    question_id: str,
    code: str,
    language: str,
    test_cases: Optional[list[dict]] = None,
) -> Submission:
    """Grade one submission with sent -> graded/failed persistence.

    The sent row is committed before the executor runs, so a crash still
    leaves state. Executor exceptions transition the row to failed and are
    swallowed into the returned row (callers decide the HTTP mapping).
    """
    repo = SqlSubmissionRepository(db)
    sent = await repo.create_sent(
        user_id=user_id,
        submission=SubmissionIn(
            question_id=question_id,
            code=code,
            language=language,
            passed=False,
        ),
    )
    try:
        results = await executor.evaluate_suite(
            language=language,
            code=code,
            test_cases=test_cases or [],
        )
    except Exception:  # noqa: BLE001 - executor failure is state, not raise
        logger.warning(
            "Grading executor failed; submission kept as failed", exc_info=True
        )
        return await repo.mark_failed(sent.id)

    passed = bool(results) and all(getattr(r, "passed", False) for r in results)
    # Empty suite cannot prove correctness; keep prior submit.py semantics
    # (passed=False when no results) by treating empty as not passed.
    if not results:
        passed = False
    return await repo.mark_graded(
        sent.id, passed=passed, error_signature=_error_signature(results)
    )
