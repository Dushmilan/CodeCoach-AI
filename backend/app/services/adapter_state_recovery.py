"""Stale adapter-state recovery — flip stuck sent rows to terminal states.

A crashed process can leave coaching/execution/submission rows in sent (or
submitted) past the recovery window. This worker marks them timeout/failed
so they never stay stuck and remain observable. It never re-invokes
external providers — recovery is a local state transition only.

Callers: cron/apscheduler, lifespan background task, or admin endpoint.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sql_coaching_interaction_repository import (
    SqlCoachingInteractionRepository,
)
from app.repositories.sql_execution_job_repository import SqlExecutionJobRepository
from app.repositories.sql_submission_repository import SqlSubmissionRepository

logger = logging.getLogger(__name__)

STALE_ERROR_CODE = "STALE_RECOVERY"
STALE_ERROR_MESSAGE = "Recovered stuck sent state (worker timeout)"


async def recover_stale_adapter_state(
    db: AsyncSession,
    *,
    older_than_minutes: int = 5,
    limit: int = 100,
    now: datetime | None = None,
) -> dict[str, int]:
    """Mark stale sent/submitted rows terminal; return per-table counts."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(minutes=older_than_minutes)
    coaching = SqlCoachingInteractionRepository(db)
    executions = SqlExecutionJobRepository(db)
    submissions = SqlSubmissionRepository(db)
    counts = {"coaching_interactions": 0, "execution_jobs": 0, "submissions": 0}

    try:
        stale_coaching = await coaching.list_stale(older_than=cutoff, limit=limit)
    except Exception:  # noqa: BLE001 - recovery must degrade open
        logger.warning("Stale coaching scan failed", exc_info=True)
        stale_coaching = []
    for row in stale_coaching:
        try:
            await coaching.mark_failed(
                row.id,
                status="timeout",
                error_code=STALE_ERROR_CODE,
                error_message=STALE_ERROR_MESSAGE,
            )
            counts["coaching_interactions"] += 1
        except Exception:  # noqa: BLE001
            logger.warning(
                "Failed to recover coaching interaction %s", row.id, exc_info=True
            )

    try:
        stale_jobs = await executions.list_stale(older_than=cutoff, limit=limit)
    except Exception:  # noqa: BLE001
        logger.warning("Stale execution scan failed", exc_info=True)
        stale_jobs = []
    for row in stale_jobs:
        try:
            await executions.mark_failed(
                row.id,
                status="timeout",
                error_code=STALE_ERROR_CODE,
                error_message=STALE_ERROR_MESSAGE,
            )
            counts["execution_jobs"] += 1
        except Exception:  # noqa: BLE001
            logger.warning("Failed to recover execution job %s", row.id, exc_info=True)

    try:
        stale_subs = await submissions.list_stale(older_than=cutoff, limit=limit)
    except Exception:  # noqa: BLE001
        logger.warning("Stale submission scan failed", exc_info=True)
        stale_subs = []
    for row in stale_subs:
        try:
            await submissions.mark_failed(row.id)
            counts["submissions"] += 1
        except Exception:  # noqa: BLE001
            logger.warning("Failed to recover submission %s", row.id, exc_info=True)

    if sum(counts.values()):
        logger.info("Recovered stale adapter state: %s", counts)
    return counts
