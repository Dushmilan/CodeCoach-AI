import uuid
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mistake_schemas import ReviewCard
from app.models.orm import ReviewCardORM
from app.ports.review_repository import ReviewRepository


class SqlReviewRepository(ReviewRepository):
    """PostgreSQL/Supabase implementation of the review-card repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _orm_to_schema(orm: ReviewCardORM) -> ReviewCard:
        return ReviewCard(
            id=orm.id,
            user_id=orm.user_id,
            question_id=orm.question_id,
            error_signature=orm.error_signature,
            state=orm.state,
            ease=orm.ease,
            interval_days=orm.interval_days,
            repetitions=orm.repetitions,
            lapses=orm.lapses,
            due_at=orm.due_at,
            last_reviewed_at=orm.last_reviewed_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    @staticmethod
    def _schema_to_values(card: ReviewCard) -> dict:
        return {
            "id": card.id,
            "user_id": card.user_id,
            "question_id": card.question_id,
            "error_signature": card.error_signature,
            "state": card.state,
            "ease": card.ease,
            "interval_days": card.interval_days,
            "repetitions": card.repetitions,
            "lapses": card.lapses,
            "due_at": card.due_at,
            "last_reviewed_at": card.last_reviewed_at,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
        }

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex

    async def get(self, user_id: str, card_id: str) -> Optional[ReviewCard]:
        result = await self.session.execute(
            select(ReviewCardORM).where(
                ReviewCardORM.id == card_id,
                ReviewCardORM.user_id == user_id,
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def list_for_question(
        self, user_id: str, question_id: str
    ) -> Sequence[ReviewCard]:
        result = await self.session.execute(
            select(ReviewCardORM)
            .where(
                ReviewCardORM.user_id == user_id,
                ReviewCardORM.question_id == question_id,
            )
            .order_by(ReviewCardORM.created_at.asc())
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]

    async def list_due(
        self, *, user_id: str, now: datetime, limit: int = 20
    ) -> Sequence[ReviewCard]:
        result = await self.session.execute(
            select(ReviewCardORM)
            .where(
                ReviewCardORM.user_id == user_id,
                ReviewCardORM.state == "scheduled",
                ReviewCardORM.due_at <= now,
            )
            .order_by(ReviewCardORM.due_at.asc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]

    async def save(self, card: ReviewCard) -> ReviewCard:
        """Atomic upsert on the natural key (race-safe under concurrency).

        Targets the unique index columns directly - ``ON CONFLICT (cols)`` -
        because the uniqueness is enforced by a unique INDEX, not a named
        table constraint.
        """
        values = self._schema_to_values(card)
        if not values["id"]:
            values["id"] = self._new_id()

        mutable = {
            key: values[key]
            for key in (
                "state",
                "ease",
                "interval_days",
                "repetitions",
                "lapses",
                "due_at",
                "last_reviewed_at",
                "updated_at",
            )
        }
        stmt = (
            pg_insert(ReviewCardORM)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["user_id", "question_id", "error_signature"],
                set_=mutable,
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()

        saved = await self.session.execute(
            select(ReviewCardORM).where(
                ReviewCardORM.user_id == card.user_id,
                ReviewCardORM.question_id == card.question_id,
                ReviewCardORM.error_signature == card.error_signature,
            )
        )
        return self._orm_to_schema(saved.scalar_one())
