"""Spaced-repetition review endpoints (mistake-memory phase 2)."""

from datetime import datetime, timezone

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_review_service
from app.models.auth_schemas import UserResponse
from app.models.mistake_schemas import DueReviewsResponse, GradeIn, GradeResponse
from app.services.review_service import CardNotFoundError, ReviewService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/due", response_model=DueReviewsResponse)
async def get_due_reviews(
    limit: int = Query(20, ge=1, le=100, description="Max due cards to return"),
    current_user: UserResponse = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """Return the user's review cards whose re-solve time has come."""
    try:
        cards = await service.due(user_id=current_user.id, now=_utc_now(), limit=limit)
        return DueReviewsResponse(cards=list(cards), total=len(cards))
    except Exception:
        logger.exception("Failed to list due reviews for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to list due reviews")


@router.post("/{card_id}/grade", response_model=GradeResponse)
async def grade_review(
    card_id: str,
    grade: GradeIn,
    current_user: UserResponse = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """Grade one review card (SM-2 quality 0..5) and return its new schedule."""
    try:
        card = await service.grade(
            user_id=current_user.id,
            card_id=card_id,
            quality=grade.quality,
            now=_utc_now(),
        )
        return GradeResponse(card=card)
    except CardNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception:
        logger.exception(
            "Failed to grade review %s for user %s", card_id, current_user.id
        )
        raise HTTPException(status_code=500, detail="Failed to grade review")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
