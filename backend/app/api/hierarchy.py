"""Admin hierarchy API (Issue #159 Task 6) — read-only admin tree.

``GET /api/admin/hierarchy`` (admin/super_admin only via ``require_admin``)
returns the professor → courses/classrooms tree assembled by
``HierarchyService`` from existing ports + ``ClassAnalyticsService``.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth_deps import require_admin
from app.api.dependencies import get_hierarchy_service
from app.models.auth_schemas import UserResponse
from app.services.hierarchy_service import HierarchyService

logger = logging.getLogger(__name__)
router = APIRouter()


class HierarchyCourseOut(BaseModel):
    """Course row with a lesson count for the admin tree."""

    id: str
    title: str
    lessons: int


class HierarchyClassroomOut(BaseModel):
    """Classroom row with staff, roster size, and class average."""

    id: str
    name: str
    invite_code: str
    tas: list[str]
    students: int
    avg_completion: float


class HierarchyProfessorOut(BaseModel):
    """One professor root with owned courses and classrooms."""

    id: str
    username: str
    courses: list[HierarchyCourseOut]
    classrooms: list[HierarchyClassroomOut]


class HierarchyOut(BaseModel):
    """Exact Task 6 brief shape: professors[] of courses[] + classrooms[]."""

    professors: list[HierarchyProfessorOut]


@router.get("/hierarchy", response_model=HierarchyOut)
async def admin_hierarchy(
    service: HierarchyService = Depends(get_hierarchy_service),
    current_user: UserResponse = Depends(require_admin),
):
    """Full admin tree. 403 for non-admins via ``require_admin``."""
    logger.info("Admin hierarchy requested by %s", current_user.id)
    return await service.admin_tree()
