import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.adapter_state_schemas import CoachingInteraction
from app.models.orm import CoachingInteractionORM
from app.ports.coaching_interaction_repository import CoachingInteractionRepository


class SqlCoachingInteractionRepository(CoachingInteractionRepository):
    """PostgreSQL/Supabase implementation of coaching interaction state."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _orm_to_schema(orm: CoachingInteractionORM) -> CoachingInteraction:
        return CoachingInteraction(
            id=orm.id,
            user_id=orm.user_id,
            question_id=orm.question_id,
            lesson_id=orm.lesson_id,
            mode=orm.mode,
            language=orm.language,
            problem_hash=orm.problem_hash,
            code_hash=orm.code_hash,
            idempotency_key=orm.idempotency_key,
            status=orm.status,
            request_payload=orm.request_payload or {},
            response_payload=orm.response_payload,
            error_code=orm.error_code,
            error_message=orm.error_message,
            model=orm.model,
            input_tokens=orm.input_tokens or 0,
            output_tokens=orm.output_tokens or 0,
            retry_count=orm.retry_count or 0,
            request_id=orm.request_id,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            completed_at=orm.completed_at,
        )

    async def create_sent(
        self,
        *,
        user_id: str,
        question_id: Optional[str],
        mode: str,
        language: str,
        problem_hash: str,
        code_hash: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
        lesson_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CoachingInteraction:
        now = datetime.now(timezone.utc)
        orm = CoachingInteractionORM(
            id=uuid.uuid4().hex,
            user_id=user_id,
            question_id=question_id,
            lesson_id=lesson_id,
            mode=mode,
            language=language,
            problem_hash=problem_hash,
            code_hash=code_hash,
            idempotency_key=idempotency_key,
            status="sent",
            request_payload=request_payload,
            response_payload=None,
            error_code=None,
            error_message=None,
            retry_count=0,
            request_id=request_id,
            created_at=now,
            updated_at=now,
            completed_at=None,
        )
        self.session.add(orm)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def get(self, interaction_id: str) -> Optional[CoachingInteraction]:
        result = await self.session.execute(
            select(CoachingInteractionORM).where(
                CoachingInteractionORM.id == interaction_id
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def get_by_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Optional[CoachingInteraction]:
        result = await self.session.execute(
            select(CoachingInteractionORM).where(
                CoachingInteractionORM.user_id == user_id,
                CoachingInteractionORM.idempotency_key == idempotency_key,
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def _transition(
        self, interaction_id: str, status: str, **fields: Any
    ) -> CoachingInteraction:
        result = await self.session.execute(
            select(CoachingInteractionORM).where(
                CoachingInteractionORM.id == interaction_id
            )
        )
        orm = result.scalar_one()
        orm.status = status
        for key, value in fields.items():
            setattr(orm, key, value)
        orm.updated_at = datetime.now(timezone.utc)
        if status in ("completed", "failed", "timeout", "rate_limited"):
            orm.completed_at = datetime.now(timezone.utc)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def mark_completed(
        self,
        interaction_id: str,
        *,
        response_payload: Optional[dict[str, Any]] = None,
    ) -> CoachingInteraction:
        return await self._transition(
            interaction_id, "completed", response_payload=response_payload
        )

    async def mark_failed(
        self,
        interaction_id: str,
        *,
        status: str = "failed",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> CoachingInteraction:
        return await self._transition(
            interaction_id,
            status,
            error_code=error_code,
            error_message=error_message,
        )

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> Sequence[CoachingInteraction]:
        result = await self.session.execute(
            select(CoachingInteractionORM)
            .where(CoachingInteractionORM.user_id == user_id)
            .order_by(CoachingInteractionORM.created_at.desc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]

    async def list_stale(
        self, *, older_than: datetime, limit: int = 100
    ) -> Sequence[CoachingInteraction]:
        result = await self.session.execute(
            select(CoachingInteractionORM)
            .where(
                CoachingInteractionORM.status.in_(["sent", "submitted"]),
                CoachingInteractionORM.created_at < older_than,
            )
            .order_by(CoachingInteractionORM.created_at.asc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]
