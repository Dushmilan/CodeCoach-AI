import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import SubmissionORM
from app.models.submission_schemas import Submission, SubmissionIn
from app.ports.submission_repository import SubmissionRepository


class SqlSubmissionRepository(SubmissionRepository):
    """PostgreSQL/Supabase implementation of the submission repository."""

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
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(orm)
        await self.session.commit()
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

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

    async def count_attempts(self, user_id: str, question_id: str) -> int:
        result = await self.session.execute(
            select(func.count(SubmissionORM.id)).where(
                SubmissionORM.user_id == user_id,
                SubmissionORM.question_id == question_id,
            )
        )
        return int(result.scalar_one())
