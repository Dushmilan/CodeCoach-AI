import uuid
from datetime import date, datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import (
    RateLimitEventORM,
    UserUsageEventORM,
    UserDailyUsageORM,
)
from app.models.usage_schemas import (
    DailyUsage,
    RateLimitBreakdownRow,
    RateLimitEventOut,
    UsageEventOut,
    UserUsageTotals,
)
from app.ports.usage_repository import UsageRepository


class SqlUsageRepository(UsageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_event(
        self,
        *,
        user_id: str,
        provider: str,
        model: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        orm = UserUsageEventORM(
            id=uuid.uuid4().hex,
            user_id=user_id,
            provider=provider,
            model=model,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self.session.add(orm)
        await self.session.commit()

    async def increment_daily(
        self,
        *,
        user_id: str,
        usage_date: date,
        input_tokens: int,
        output_tokens: int,
        request_count: int = 1,
    ) -> None:
        values = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "usage_date": usage_date,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "request_count": request_count,
        }
        dialect = self.session.bind.dialect.name if self.session.bind else "mysql"
        if dialect == "postgresql":
            stmt = pg_insert(UserDailyUsageORM).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    UserDailyUsageORM.user_id,
                    UserDailyUsageORM.usage_date,
                ],
                set_={
                    "input_tokens": UserDailyUsageORM.input_tokens + input_tokens,
                    "output_tokens": UserDailyUsageORM.output_tokens + output_tokens,
                    "request_count": UserDailyUsageORM.request_count + request_count,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        else:
            stmt = mysql_insert(UserDailyUsageORM).values(**values)
            stmt = stmt.on_duplicate_key_update(
                input_tokens=UserDailyUsageORM.input_tokens + input_tokens,
                output_tokens=UserDailyUsageORM.output_tokens + output_tokens,
                request_count=UserDailyUsageORM.request_count + request_count,
                updated_at=datetime.now(timezone.utc),
            )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_daily(self, user_id: str, usage_date: date) -> Optional[DailyUsage]:
        result = await self.session.execute(
            select(UserDailyUsageORM).where(
                UserDailyUsageORM.user_id == user_id,
                UserDailyUsageORM.usage_date == usage_date,
            )
        )
        orm = result.scalar_one_or_none()
        if orm is None:
            return None
        return DailyUsage(
            user_id=orm.user_id,
            usage_date=orm.usage_date,
            input_tokens=orm.input_tokens,
            output_tokens=orm.output_tokens,
            request_count=orm.request_count,
        )

    async def recent_events(
        self, user_id: str, limit: int = 50
    ) -> Sequence[UsageEventOut]:
        result = await self.session.execute(
            select(UserUsageEventORM)
            .where(UserUsageEventORM.user_id == user_id)
            .order_by(UserUsageEventORM.created_at.desc())
            .limit(limit)
        )
        return [self._event_to_out(orm) for orm in result.scalars().all()]

    async def user_totals(self, user_id: str, since: datetime) -> DailyUsage:
        result = await self.session.execute(
            select(
                func.coalesce(func.sum(UserUsageEventORM.input_tokens), 0),
                func.coalesce(func.sum(UserUsageEventORM.output_tokens), 0),
                func.count(UserUsageEventORM.id),
            ).where(
                UserUsageEventORM.user_id == user_id,
                UserUsageEventORM.created_at >= since,
            )
        )
        input_tokens, output_tokens, _ = result.one()
        return DailyUsage(
            user_id=user_id,
            usage_date=since.date(),
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
        )

    async def all_user_totals(
        self, since: datetime, limit: int = 100
    ) -> Sequence[UserUsageTotals]:
        result = await self.session.execute(
            select(
                UserUsageEventORM.user_id,
                func.coalesce(func.sum(UserUsageEventORM.input_tokens), 0),
                func.coalesce(func.sum(UserUsageEventORM.output_tokens), 0),
                func.count(UserUsageEventORM.id),
            )
            .where(UserUsageEventORM.created_at >= since)
            .group_by(UserUsageEventORM.user_id)
            .order_by(func.sum(UserUsageEventORM.input_tokens).desc())
            .limit(limit)
        )
        return [
            UserUsageTotals(
                user_id=user_id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                call_count=int(call_count),
            )
            for user_id, input_tokens, output_tokens, call_count in result.all()
        ]

    async def all_daily(
        self, user_id: str, since: date, limit: int = 30
    ) -> Sequence[DailyUsage]:
        result = await self.session.execute(
            select(UserDailyUsageORM)
            .where(
                UserDailyUsageORM.user_id == user_id,
                UserDailyUsageORM.usage_date >= since,
            )
            .order_by(UserDailyUsageORM.usage_date.desc())
            .limit(limit)
        )
        return [
            DailyUsage(
                user_id=orm.user_id,
                usage_date=orm.usage_date,
                input_tokens=orm.input_tokens,
                output_tokens=orm.output_tokens,
                request_count=orm.request_count,
            )
            for orm in result.scalars().all()
        ]

    @staticmethod
    def _event_to_out(orm: UserUsageEventORM) -> UsageEventOut:
        return UsageEventOut(
            id=orm.id,
            user_id=orm.user_id,
            provider=orm.provider,
            model=orm.model,
            endpoint=orm.endpoint,
            input_tokens=orm.input_tokens,
            output_tokens=orm.output_tokens,
            created_at=orm.created_at,
        )

    async def add_rate_limit_event(
        self,
        *,
        user_id: Optional[str],
        ip: str,
        reason: str,
        endpoint: str,
    ) -> None:
        orm = RateLimitEventORM(
            id=uuid.uuid4().hex,
            user_id=user_id,
            ip=ip,
            reason=reason,
            endpoint=endpoint,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(orm)
        await self.session.commit()

    async def recent_rate_limit_events(
        self, limit: int = 100
    ) -> Sequence[RateLimitEventOut]:
        result = await self.session.execute(
            select(RateLimitEventORM)
            .order_by(RateLimitEventORM.created_at.desc())
            .limit(limit)
        )
        return [self._rl_event_to_out(orm) for orm in result.scalars().all()]

    async def count_rate_limit_events(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(RateLimitEventORM.id)).where(
                RateLimitEventORM.created_at >= since
            )
        )
        return int(result.scalar_one())

    async def rate_limit_event_breakdown(
        self, since: datetime, field: str = "reason"
    ) -> Sequence[RateLimitBreakdownRow]:
        column = getattr(RateLimitEventORM, field, None)
        if column is None:
            column = RateLimitEventORM.reason
        result = await self.session.execute(
            select(
                column,
                func.count(RateLimitEventORM.id),
            )
            .where(RateLimitEventORM.created_at >= since)
            .group_by(column)
            .order_by(func.count(RateLimitEventORM.id).desc())
        )
        return [
            RateLimitBreakdownRow(key=value, count=int(count))
            for value, count in result.all()
        ]

    @staticmethod
    def _rl_event_to_out(orm: RateLimitEventORM) -> RateLimitEventOut:
        return RateLimitEventOut(
            id=orm.id,
            user_id=orm.user_id,
            ip=orm.ip,
            reason=orm.reason,
            endpoint=orm.endpoint,
            created_at=orm.created_at,
        )
