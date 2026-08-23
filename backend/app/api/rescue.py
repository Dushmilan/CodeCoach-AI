"""Durable rescue re-surface queue endpoints (Ideas #4).

Every abandoned problem becomes a "due tomorrow morning" re-surface item.
Action endpoints answer uniformly with {"item": RescueItem | null}; a null
item is a normal outcome, never an error.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_rescue_service
from app.models.auth_schemas import UserResponse
from app.models.rescue_schemas import (
    RescueAbandonRequest,
    RescueActionResponse,
    RescueListResponse,
)
from app.services.rescue_service import RescueService

logger = logging.getLogger(__name__)

router = APIRouter()

_FOREIGN_KEY_VIOLATION = "23503"
_UNIQUE_VIOLATION = "23505"


def _integrity_sqlstate(exc: IntegrityError) -> Optional[str]:
    """Best-effort SQLSTATE from the driver exception (asyncpg/psycopg)."""
    orig = getattr(exc, "orig", None)
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


@router.get("/due", response_model=RescueListResponse)
async def get_due_rescues(
    limit: int = Query(50, ge=1, le=200, description="Max due items to return"),
    current_user: UserResponse = Depends(get_current_user),
    service: RescueService = Depends(get_rescue_service),
):
    """Open queue rows whose resurface time has come, oldest first."""
    items = await service.due(
        user_id=current_user.id,
        now=datetime.now(timezone.utc),
        limit=limit,
    )
    return RescueListResponse(items=list(items), total=len(items))


@router.post("/{question_id}/abandon", response_model=RescueActionResponse)
async def abandon_question(
    question_id: str,
    payload: Optional[RescueAbandonRequest] = None,
    current_user: UserResponse = Depends(get_current_user),
    service: RescueService = Depends(get_rescue_service),
):
    """Record an abandonment and schedule tomorrow-morning resurface.

    Returns ``{"item": null}`` when this question was previously dismissed -
    dismissals are permanent by contract.
    """
    body = payload or RescueAbandonRequest()
    try:
        item = await service.abandon(
            user_id=current_user.id,
            question_id=question_id,
            now=datetime.now(timezone.utc),
            tz_offset_minutes=body.tz_offset_minutes,
        )
    except IntegrityError as exc:
        sqlstate = _integrity_sqlstate(exc)
        if sqlstate == _FOREIGN_KEY_VIOLATION:
            # foreign_key_violation - the question does not exist.
            logger.info(
                "rescue abandon for unknown question %s (user %s)",
                question_id,
                current_user.id,
            )
            raise HTTPException(status_code=404, detail="Question not found")
        if sqlstate == _UNIQUE_VIOLATION:
            # unique_violation on the partial index: a concurrent abandon
            # already recorded this row. Answer idempotently with whatever is
            # open now (may itself be gone again) instead of a bogus 404.
            logger.info(
                "rescue abandon race for %s (user %s); returning current row",
                question_id,
                current_user.id,
            )
            existing = await service.open_item(
                user_id=current_user.id, question_id=question_id
            )
            return RescueActionResponse(item=existing)
        raise
    except Exception:
        logger.exception(
            "Failed to record rescue abandonment for user %s", current_user.id
        )
        raise HTTPException(status_code=500, detail="Failed to record abandonment")
    return RescueActionResponse(item=item)


@router.post("/{question_id}/complete", response_model=RescueActionResponse)
async def complete_question(
    question_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: RescueService = Depends(get_rescue_service),
):
    """Close the open row after solving (no-op if nothing was open)."""
    item = await service.complete(
        user_id=current_user.id,
        question_id=question_id,
        now=datetime.now(timezone.utc),
    )
    return RescueActionResponse(item=item)


@router.post("/{question_id}/dismiss", response_model=RescueActionResponse)
async def dismiss_question(
    question_id: str,
    current_user: UserResponse = Depends(get_current_user),
    service: RescueService = Depends(get_rescue_service),
):
    """Honour "never show me this problem's nudges again" permanently."""
    item = await service.dismiss(
        user_id=current_user.id,
        question_id=question_id,
        now=datetime.now(timezone.utc),
    )
    return RescueActionResponse(item=item)
