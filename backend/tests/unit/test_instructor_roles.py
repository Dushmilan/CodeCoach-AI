"""Instructor role guards (Issue #159, phase 2).

Professors own classrooms/courses; demonstrators (TAs) get limited access:
roster + analytics + coaching only. See TA permission matrix in #159.
"""

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.auth_schemas import UserResponse


def _user(role: str) -> UserResponse:
    return UserResponse(
        id="u1",
        username="instructor",
        email="instructor@codecoach.ai",
        created_at=datetime.now(timezone.utc),
        role=role,
    )


class TestRequireProfessor:
    @pytest.mark.asyncio
    async def test_allows_professor_and_admins(self):
        from app.api.auth_deps import require_professor

        for role in ("professor", "admin", "super_admin"):
            result = await require_professor(_user(role))
            assert result.role == role

    @pytest.mark.asyncio
    async def test_denies_student_and_ta(self):
        from app.api.auth_deps import require_professor

        for role in ("user", "ta"):
            with pytest.raises(HTTPException) as exc:
                await require_professor(_user(role))
            assert exc.value.status_code == 403


class TestRequireInstructor:
    @pytest.mark.asyncio
    async def test_allows_professor_ta_and_admins(self):
        from app.api.auth_deps import require_instructor

        for role in ("professor", "ta", "admin", "super_admin"):
            result = await require_instructor(_user(role))
            assert result.role == role

    @pytest.mark.asyncio
    async def test_denies_student(self):
        from app.api.auth_deps import require_instructor

        with pytest.raises(HTTPException) as exc:
            await require_instructor(_user("user"))
        assert exc.value.status_code == 403


class TestTAPermissionMatrix:
    def test_roster_management_is_professor_only(self):
        from app.api.auth_deps import instructor_can_manage_roster

        assert instructor_can_manage_roster("professor") is True
        assert instructor_can_manage_roster("admin") is True
        assert instructor_can_manage_roster("super_admin") is True
        assert instructor_can_manage_roster("ta") is False
        assert instructor_can_manage_roster("user") is False

    def test_course_editing_is_professor_only(self):
        from app.api.auth_deps import instructor_can_edit_courses

        assert instructor_can_edit_courses("professor") is True
        assert instructor_can_edit_courses("admin") is True
        assert instructor_can_edit_courses("ta") is False
        assert instructor_can_edit_courses("user") is False

    def test_analytics_visible_to_professor_and_ta(self):
        from app.api.auth_deps import instructor_can_view_analytics

        assert instructor_can_view_analytics("professor") is True
        assert instructor_can_view_analytics("ta") is True
        assert instructor_can_view_analytics("user") is False
