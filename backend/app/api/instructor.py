"""Instructor API (Issue #159, phase 2) — read-only class views.

Guarded by ``require_instructor`` (professor + TA + admins). Aggregates only
data that already exists per student (progress + submissions); no new tables,
no writes. Roster is passed explicitly until phase-1 classroom tables land.
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.api.auth_deps import require_instructor
from app.api.dependencies import get_class_analytics_service
from app.models.analytics_schemas import ClassAnalyticsResponse
from app.models.auth_schemas import UserResponse
from app.services.class_analytics_service import ClassAnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/class-analytics", response_model=ClassAnalyticsResponse)
async def class_analytics(
    user_ids: str = Query(default="", description="CSV roster of user IDs"),
    total_lessons: int = Query(default=10, ge=0),
    service: ClassAnalyticsService = Depends(get_class_analytics_service),
    current_user: UserResponse = Depends(require_instructor),
):
    roster = [u.strip() for u in user_ids.split(",") if u.strip()]
    try:
        return await service.class_overview(roster, total_lessons=total_lessons)
    except Exception:
        logger.exception(
            "Failed to derive class analytics for instructor %s", current_user.id
        )
        return ClassAnalyticsResponse(
            total_students=len(roster),
            avg_completion=0.0,
            avg_solved=0.0,
            students=[],
        )
