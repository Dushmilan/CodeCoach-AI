"""SQL implementation of ClassroomRepository (PostgreSQL only)."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.orm import ClassroomEnrollmentORM, ClassroomORM, CourseORM
from app.ports.classroom_repository import ClassroomRepository

_ALLOWED_ROLES = ("student", "ta")


def _is_unique_violation(exc: IntegrityError) -> bool:
    """True only for unique violations (Postgres sqlstate 23505).

    Falls back to the constraint name because the message text alone
    (e.g. a column name) also appears in NOT NULL / FK failures.
    """
    if getattr(exc.orig, "sqlstate", None) == "23505":
        return True
    return "uq_classrooms_invite_code" in str(exc.orig)


class DuplicateInviteCodeError(ValueError):
    """Raised when a classroom invite_code collides (unique constraint).

    Subclasses ValueError so the API layer can translate it to a 409
    Conflict without importing SQLAlchemy error types.
    """


class SqlClassroomRepository(ClassroomRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

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
        orm = ClassroomORM(
            id=uuid.uuid4().hex,
            course_id=course_id,
            owner_id=owner_id,
            name=name,
            invite_code=invite_code,
            term=term,
            schedule=schedule,
        )
        self.session.add(orm)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            if _is_unique_violation(exc):
                raise DuplicateInviteCodeError(
                    f"invite code {invite_code!r} already exists"
                ) from exc
            raise
        return orm

    async def list_owned_by_professor(self, owner_id: str) -> list[ClassroomORM]:
        result = await self.session.execute(
            select(ClassroomORM)
            .where(ClassroomORM.owner_id == owner_id)
            .order_by(ClassroomORM.name)
        )
        return list(result.scalars().all())

    async def list_for_ta(self, user_id: str) -> list[ClassroomORM]:
        result = await self.session.execute(
            select(ClassroomORM)
            .join(
                ClassroomEnrollmentORM,
                ClassroomEnrollmentORM.classroom_id == ClassroomORM.id,
            )
            .where(
                ClassroomEnrollmentORM.user_id == user_id,
                ClassroomEnrollmentORM.role == "ta",
            )
            .order_by(ClassroomORM.name)
        )
        return list(result.scalars().all())

    async def get_classroom_by_id(self, classroom_id: str) -> Optional[ClassroomORM]:
        result = await self.session.execute(
            select(ClassroomORM).where(ClassroomORM.id == classroom_id)
        )
        return result.scalar_one_or_none()

    async def list_classroom_student_ids(self, classroom_id: str) -> list[str]:
        result = await self.session.execute(
            select(ClassroomEnrollmentORM.user_id)
            .where(
                ClassroomEnrollmentORM.classroom_id == classroom_id,
                ClassroomEnrollmentORM.role == "student",
            )
            .order_by(ClassroomEnrollmentORM.user_id)
        )
        return list(result.scalars().all())

    async def list_classroom_student_ids_by_room(
        self, classroom_ids: list[str]
    ) -> dict[str, list[str]]:
        """One IN query for many rooms (Issue #179). Unknown ids -> []."""
        ids = list(dict.fromkeys(classroom_ids))
        grouped: dict[str, list[str]] = {cid: [] for cid in ids}
        if not ids:
            return grouped
        result = await self.session.execute(
            select(
                ClassroomEnrollmentORM.classroom_id,
                ClassroomEnrollmentORM.user_id,
            )
            .where(
                ClassroomEnrollmentORM.classroom_id.in_(ids),
                ClassroomEnrollmentORM.role == "student",
            )
            .order_by(
                ClassroomEnrollmentORM.classroom_id,
                ClassroomEnrollmentORM.user_id,
            )
        )
        for classroom_id, user_id in result.all():
            grouped[classroom_id].append(user_id)
        return grouped

    async def list_classroom_ta_ids(self, classroom_id: str) -> list[str]:
        result = await self.session.execute(
            select(ClassroomEnrollmentORM.user_id)
            .where(
                ClassroomEnrollmentORM.classroom_id == classroom_id,
                ClassroomEnrollmentORM.role == "ta",
            )
            .order_by(ClassroomEnrollmentORM.user_id)
        )
        return list(result.scalars().all())

    async def enroll(
        self, *, classroom_id: str, user_id: str, role: str
    ) -> ClassroomEnrollmentORM:
        if role not in _ALLOWED_ROLES:
            raise ValueError(f"role must be one of {_ALLOWED_ROLES}, got {role!r}")
        result = await self.session.execute(
            select(ClassroomEnrollmentORM).where(
                ClassroomEnrollmentORM.classroom_id == classroom_id,
                ClassroomEnrollmentORM.user_id == user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.role = role
            await self.session.commit()
            return existing
        orm = ClassroomEnrollmentORM(
            id=uuid.uuid4().hex,
            classroom_id=classroom_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(orm)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            # Lost a concurrent enroll race: re-read the winner and apply
            # role — but only on unique violations. Anything else (e.g. an
            # FK failure on a bad id) re-raises the original error.
            if not _is_unique_violation(exc):
                await self.session.rollback()
                raise
            await self.session.rollback()
            result = await self.session.execute(
                select(ClassroomEnrollmentORM).where(
                    ClassroomEnrollmentORM.classroom_id == classroom_id,
                    ClassroomEnrollmentORM.user_id == user_id,
                )
            )
            winner = result.scalar_one_or_none()
            if winner is None:
                raise
            winner.role = role
            await self.session.commit()
            return winner
        return orm

    async def set_course_owner(self, course_id: str, owner_id: str) -> None:
        await self.session.execute(
            update(CourseORM).where(CourseORM.id == course_id).values(owner_id=owner_id)
        )
        await self.session.commit()
