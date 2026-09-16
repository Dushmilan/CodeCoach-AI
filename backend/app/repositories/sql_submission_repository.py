import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import SubmissionORM
from app.models.submission_schemas import Submission, SubmissionIn
from app.ports.submission_repository import SubmissionRepository


class SqlSubmissionRepository(SubmissionRepository):
    """PostgreSQL/PostgreSQL implementation of the submission repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _orm_to_schema(orm: SubmissionORM) -> Submission:
        return Submission(
            id=orm.id,
            user_id=orm.user_id,
            question_id=orm.question_id,
            code=orm.code,
            language=orm.language,
            passed=orm.passed,
            error_signature=orm.error_signature,
            attempt_index=orm.attempt_index,
            status=getattr(orm, "status", "graded") or "graded",
            idempotency_key=getattr(orm, "idempotency_key", None),
            execution_job_id=getattr(orm, "execution_job_id", None),
            request_id=getattr(orm, "request_id", None),
            created_at=orm.created_at,
        )

    async def add(self, *, user_id: str, submission: SubmissionIn) -> Submission:
        attempt_index = await self.count_attempts(user_id, submission.question_id)
        orm = SubmissionORM(
            id=uuid.uuid4().hex,
            user_id=user_id,
            question_id=submission.question_id,
            code=submission.code,
            language=submission.language,
            passed=submission.passed,
            error_signature=submission.error_signature,
            attempt_index=attempt_index,
            status="graded",
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(orm)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def get(self, submission_id: str) -> Optional[Submission]:
        result = await self.session.execute(
            select(SubmissionORM).where(SubmissionORM.id == submission_id)
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def get_by_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Optional[Submission]:
        result = await self.session.execute(
            select(SubmissionORM).where(
                SubmissionORM.user_id == user_id,
                SubmissionORM.idempotency_key == idempotency_key,
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def create_sent(
        self, *, user_id: str, submission: SubmissionIn
    ) -> Submission:
        attempt_index = await self.count_attempts(user_id, submission.question_id)
        orm = SubmissionORM(
            id=uuid.uuid4().hex,
            user_id=user_id,
            question_id=submission.question_id,
            code=submission.code,
            language=submission.language,
            passed=False,
            error_signature=None,
            attempt_index=attempt_index,
            status="sent",
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(orm)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def mark_graded(
        self,
        submission_id: str,
        *,
        passed: bool,
        error_signature: Optional[str] = None,
    ) -> Submission:
        result = await self.session.execute(
            select(SubmissionORM).where(SubmissionORM.id == submission_id)
        )
        orm = result.scalar_one()
        orm.status = "graded"
        orm.passed = passed
        orm.error_signature = error_signature
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def mark_failed(self, submission_id: str) -> Submission:
        result = await self.session.execute(
            select(SubmissionORM).where(SubmissionORM.id == submission_id)
        )
        orm = result.scalar_one()
        orm.status = "failed"
        orm.passed = False
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def list_stale(self, *, older_than, limit: int = 100) -> Sequence[Submission]:
        result = await self.session.execute(
            select(SubmissionORM)
            .where(
                SubmissionORM.status.in_(["sent", "submitted"]),
                SubmissionORM.created_at < older_than,
            )
            .order_by(SubmissionORM.created_at.asc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> Sequence[Submission]:
        result = await self.session.execute(
            select(SubmissionORM)
            .where(SubmissionORM.user_id == user_id)
            .order_by(SubmissionORM.created_at.desc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]

    async def list_by_users(
        self, user_ids: Sequence[str], *, limit: int = 1000
    ) -> dict[str, Sequence[Submission]]:
        """Batch newest-first submissions per user in ONE window query."""
        ids = list(dict.fromkeys(user_ids))
        if not ids:
            return {}
        from sqlalchemy import func

        rn = func.row_number().over(
            partition_by=SubmissionORM.user_id,
            order_by=SubmissionORM.created_at.desc(),
        )
        inner = (
            select(SubmissionORM, rn.label("rn"))
            .where(SubmissionORM.user_id.in_(ids))
            .subquery()
        )
        result = await self.session.execute(
            select(inner).where(inner.c.rn <= limit).order_by(inner.c.created_at.desc())
        )
        grouped: dict[str, list[Submission]] = {uid: [] for uid in ids}
        for row in result.mappings().all():
            orm_kwargs = {
                col: row[col]
                for col in (
                    "id",
                    "user_id",
                    "question_id",
                    "code",
                    "language",
                    "passed",
                    "error_signature",
                    "attempt_index",
                    "status",
                    "idempotency_key",
                    "execution_job_id",
                    "request_id",
                    "created_at",
                )
                if col in row
            }
            grouped[row["user_id"]].append(
                Submission(
                    id=orm_kwargs["id"],
                    user_id=orm_kwargs["user_id"],
                    question_id=orm_kwargs["question_id"],
                    code=orm_kwargs["code"],
                    language=orm_kwargs["language"],
                    passed=orm_kwargs["passed"],
                    error_signature=orm_kwargs.get("error_signature"),
                    attempt_index=orm_kwargs["attempt_index"],
                    status=orm_kwargs.get("status") or "graded",
                    idempotency_key=orm_kwargs.get("idempotency_key"),
                    execution_job_id=orm_kwargs.get("execution_job_id"),
                    request_id=orm_kwargs.get("request_id"),
                    created_at=orm_kwargs["created_at"],
                )
            )
        return grouped

    async def count_attempts(self, user_id: str, question_id: str) -> int:
        result = await self.session.execute(
            select(func.count(SubmissionORM.id)).where(
                SubmissionORM.user_id == user_id,
                SubmissionORM.question_id == question_id,
            )
        )
        return int(result.scalar_one())
