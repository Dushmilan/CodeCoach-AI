"""ClassroomRepository — port for professor classroom persistence."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.orm import ClassroomEnrollmentORM, ClassroomORM


class ClassroomRepository(ABC):
    """Interface for classrooms, TA/student enrollments, and course owners."""

    @abstractmethod
    async def create_classroom(
        self,
        *,
        course_id: str,
        owner_id: str,
        name: str,
        invite_code: str,
        term: Optional[str] = None,
        schedule: Optional[str] = None,
    ) -> ClassroomORM:
        """Persist a new classroom owned by a professor."""
        ...

    @abstractmethod
    async def list_owned_by_professor(self, owner_id: str) -> list[ClassroomORM]:
        """Return classrooms owned by one professor (never others' rooms)."""
        ...

    @abstractmethod
    async def list_for_ta(self, user_id: str) -> list[ClassroomORM]:
        """Return classrooms where the user is enrolled with role='ta'."""
        ...

    @abstractmethod
    async def enroll(
        self, *, classroom_id: str, user_id: str, role: str
    ) -> ClassroomEnrollmentORM:
        """Upsert one enrollment on (classroom_id, user_id).

        `role` is required and must be 'student' or 'ta' — there is no
        DB check constraint, so callers must always pass it explicitly.
        """
        ...

    @abstractmethod
    async def set_course_owner(self, course_id: str, owner_id: str) -> None:
        """Point a course at a new professor owner."""
        ...
