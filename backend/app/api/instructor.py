"""Instructor API (Issue #159) — read-only class views.

Guarded by ``require_instructor`` (professor + TA + admins). Live classroom
endpoints are backed by ClassroomRepository + ClassAnalyticsService; the
legacy ``/class-analytics`` demo-backed aggregate is unchanged.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.auth_deps import PROFESSOR_ROLES, require_instructor
from app.api.dependencies import (
    get_class_analytics_service,
    get_classroom_repository,
)
from app.models.analytics_schemas import ClassAnalyticsResponse
from app.models.auth_schemas import UserResponse
from app.models.orm import ClassroomORM
from app.ports.classroom_repository import ClassroomRepository
from app.services.class_analytics_service import (
    ClassAnalyticsService,
    ClassroomNotFoundError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ClassroomOut(BaseModel):
    """Classroom row shape for instructor list/detail views."""

    id: str
    course_id: str
    owner_id: Optional[str] = None
    name: str
    invite_code: str
    term: Optional[str] = None
    schedule: Optional[str] = None


class ClassroomDetailOut(BaseModel):
    """Room + optimal-path class aggregates for one classroom."""

    classroom: ClassroomOut
    analytics: ClassAnalyticsResponse


def _room_out(room: ClassroomORM) -> ClassroomOut:
    return ClassroomOut(
        id=room.id,
        course_id=room.course_id,
        owner_id=room.owner_id,
        name=room.name,
        invite_code=room.invite_code,
        term=room.term,
        schedule=room.schedule,
    )


@router.get("/classrooms", response_model=list[ClassroomOut])
async def list_classrooms(
    repo: ClassroomRepository = Depends(get_classroom_repository),
    current_user: UserResponse = Depends(require_instructor),
):
    """Owned rooms for professors, assigned rooms for TAs."""
    if current_user.role == "ta":
        rooms = await repo.list_for_ta(current_user.id)
    else:
        rooms = await repo.list_owned_by_professor(current_user.id)
    return [_room_out(room) for room in rooms]


@router.get("/classrooms/{classroom_id}", response_model=ClassroomDetailOut)
async def classroom_detail(
    classroom_id: str,
    total_lessons: int = Query(default=10, ge=0),
    repo: ClassroomRepository = Depends(get_classroom_repository),
    service: ClassAnalyticsService = Depends(get_class_analytics_service),
    current_user: UserResponse = Depends(require_instructor),
):
    """Room + class aggregates. 404 for unknown ids, 403 when the caller
    neither owns the room (professor roles) nor is assigned to it (TA).

    Existence and authorization resolve before any aggregation runs, so a
    denied caller never triggers per-student progress/submission reads.
    """
    room = await service.get_classroom(classroom_id, classrooms=repo)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found"
        )
    if current_user.role in PROFESSOR_ROLES:
        if room.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not the owning professor of this classroom",
            )
    else:
        assigned = await repo.list_for_ta(current_user.id)
        if classroom_id not in {assigned_room.id for assigned_room in assigned}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not assigned to this classroom",
            )
    try:
        _, overview = await service.classroom_overview(
            classroom_id, total_lessons=total_lessons, classrooms=repo
        )
    except ClassroomNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found"
        )
    return ClassroomDetailOut(classroom=_room_out(room), analytics=overview)


@router.get("/class-analytics", response_model=ClassAnalyticsResponse)
async def class_analytics(
    user_ids: str = Query(default="", description="CSV roster of user IDs"),
    total_lessons: int = Query(default=10, ge=0),
    service: ClassAnalyticsService = Depends(get_class_analytics_service),
    repo: ClassroomRepository = Depends(get_classroom_repository),
    current_user: UserResponse = Depends(require_instructor),
):
    roster = [u.strip() for u in user_ids.split(",") if u.strip()]
    # Ownership scoping (#176): the legacy CSV roster must never expose
    # students outside the caller's owned (professor roles) or assigned
    # (TA) rooms. Resolve the allowed set first, then deny out-of-scope
    # ids before any per-student progress/submission reads run.
    if current_user.role == "ta":
        rooms = await repo.list_for_ta(current_user.id)
    else:
        rooms = await repo.list_owned_by_professor(current_user.id)
    allowed: set[str] = set()
    for room in rooms:
        allowed.update(await repo.list_classroom_student_ids(room.id))
    if not roster:
        return ClassAnalyticsResponse(
            total_students=0,
            avg_completion=0.0,
            avg_solved=0.0,
            students=[],
        )
    disallowed = [u for u in roster if u not in allowed]
    if disallowed:
        logger.warning(
            "Blocked out-of-scope class-analytics request by instructor %s "
            "for %d student(s)",
            current_user.id,
            len(disallowed),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for requested students",
        )
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
