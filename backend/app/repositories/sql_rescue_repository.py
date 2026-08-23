import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import RescueQueueORM
from app.models.rescue_schemas import RescueItem, RescueStatus
from app.ports.rescue_repository import RescueRepository


class SqlRescueRepository(RescueRepository):
    """PostgreSQL/Supabase implementation of the rescue re-surface queue."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _orm_to_schema(orm: RescueQueueORM) -> RescueItem:
        return RescueItem(
            id=orm.id,
            user_id=orm.user_id,
            question_id=orm.question_id,
            status=orm.status,
            first_abandoned_at=orm.first_abandoned_at,
            due_at=orm.due_at,
            resurface_count=orm.resurface_count,
            last_intervention_at=orm.last_intervention_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def create_abandoned(
        self, *, user_id: str, question_id: str, due_at: datetime, now: datetime
    ) -> RescueItem:
        orm = RescueQueueORM(
            id=uuid.uuid4().hex,
            user_id=user_id,
            question_id=question_id,
            status="abandoned",
            first_abandoned_at=now,
            due_at=due_at,
            resurface_count=0,
            created_at=now,
            updated_at=now,
        )
        self.session.add(orm)
        await self.session.commit()
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def get(self, user_id: str, question_id: str) -> Optional[RescueItem]:
        result = await self.session.execute(
            select(RescueQueueORM).where(
                RescueQueueORM.user_id == user_id,
                RescueQueueORM.question_id == question_id,
                RescueQueueORM.status == "abandoned",
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def latest(self, user_id: str, question_id: str) -> Optional[RescueItem]:
        result = await self.session.execute(
            select(RescueQueueORM)
            .where(
                RescueQueueORM.user_id == user_id,
                RescueQueueORM.question_id == question_id,
            )
            .order_by(RescueQueueORM.created_at.desc())
            .limit(1)
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def reschedule(
        self, *, user_id: str, question_id: str, due_at: datetime, now: datetime
    ) -> Optional[RescueItem]:
        await self.session.execute(
            update(RescueQueueORM)
            .where(
                RescueQueueORM.user_id == user_id,
                RescueQueueORM.question_id == question_id,
                RescueQueueORM.status == "abandoned",
            )
            .values(
                due_at=due_at,
                resurface_count=RescueQueueORM.resurface_count + 1,
                updated_at=now,
            )
        )
        await self.session.commit()
        return await self.get(user_id=user_id, question_id=question_id)

    async def close(
        self,
        *,
        user_id: str,
        question_id: str,
        status: RescueStatus,
        now: datetime,
    ) -> Optional[RescueItem]:
        result = await self.session.execute(
            update(RescueQueueORM)
            .where(
                RescueQueueORM.user_id == user_id,
                RescueQueueORM.question_id == question_id,
                RescueQueueORM.status == "abandoned",
            )
            .values(status=status, updated_at=now)
            .returning(RescueQueueORM.id)
        )
        closed_id = result.scalar_one_or_none()
        await self.session.commit()
        if closed_id is None:
            return None
        refreshed = await self.session.execute(
            select(RescueQueueORM).where(RescueQueueORM.id == closed_id)
        )
        return self._orm_to_schema(refreshed.scalar_one())

    async def list_due(
        self, *, user_id: str, now: datetime, limit: int = 50
    ) -> Sequence[RescueItem]:
        result = await self.session.execute(
            select(RescueQueueORM)
            .where(
                RescueQueueORM.user_id == user_id,
                RescueQueueORM.status == "abandoned",
                RescueQueueORM.due_at <= now,
            )
            .order_by(RescueQueueORM.due_at.asc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]
