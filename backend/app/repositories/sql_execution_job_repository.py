import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.adapter_state_schemas import ExecutionJob
from app.models.orm import ExecutionJobORM
from app.ports.execution_job_repository import ExecutionJobRepository


class SqlExecutionJobRepository(ExecutionJobRepository):
    """PostgreSQL/Supabase implementation of execution job state."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _orm_to_schema(orm: ExecutionJobORM) -> ExecutionJob:
        return ExecutionJob(
            id=orm.id,
            user_id=orm.user_id,
            question_id=orm.question_id,
            language=orm.language,
            code_hash=orm.code_hash,
            idempotency_key=orm.idempotency_key,
            status=orm.status,
            request_payload=orm.request_payload or {},
            response_payload=orm.response_payload,
            test_results=orm.test_results,
            error_code=orm.error_code,
            error_message=orm.error_message,
            execution_time_ms=orm.execution_time_ms,
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
        language: str,
        code_hash: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
        request_id: Optional[str] = None,
    ) -> ExecutionJob:
        now = datetime.now(timezone.utc)
        orm = ExecutionJobORM(
            id=uuid.uuid4().hex,
            user_id=user_id,
            question_id=question_id,
            language=language,
            code_hash=code_hash,
            idempotency_key=idempotency_key,
            status="sent",
            request_payload=request_payload,
            response_payload=None,
            test_results=None,
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

    async def get(self, job_id: str) -> Optional[ExecutionJob]:
        result = await self.session.execute(
            select(ExecutionJobORM).where(ExecutionJobORM.id == job_id)
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def get_by_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Optional[ExecutionJob]:
        result = await self.session.execute(
            select(ExecutionJobORM).where(
                ExecutionJobORM.user_id == user_id,
                ExecutionJobORM.idempotency_key == idempotency_key,
            )
        )
        orm = result.scalar_one_or_none()
        return self._orm_to_schema(orm) if orm else None

    async def _transition(
        self, job_id: str, status: str, **fields: Any
    ) -> ExecutionJob:
        result = await self.session.execute(
            select(ExecutionJobORM).where(ExecutionJobORM.id == job_id)
        )
        orm = result.scalar_one()
        orm.status = status
        for key, value in fields.items():
            setattr(orm, key, value)
        orm.updated_at = datetime.now(timezone.utc)
        if status in ("executed", "failed", "timeout", "cancelled"):
            orm.completed_at = datetime.now(timezone.utc)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        await self.session.refresh(orm)
        return self._orm_to_schema(orm)

    async def mark_executed(
        self,
        job_id: str,
        *,
        response_payload: Optional[dict[str, Any]] = None,
        test_results: Optional[list[dict[str, Any]]] = None,
        execution_time_ms: Optional[int] = None,
    ) -> ExecutionJob:
        return await self._transition(
            job_id,
            "executed",
            response_payload=response_payload,
            test_results=test_results,
            execution_time_ms=execution_time_ms,
        )

    async def mark_failed(
        self,
        job_id: str,
        *,
        status: str = "failed",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ExecutionJob:
        return await self._transition(
            job_id,
            status,
            error_code=error_code,
            error_message=error_message,
        )

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> Sequence[ExecutionJob]:
        result = await self.session.execute(
            select(ExecutionJobORM)
            .where(ExecutionJobORM.user_id == user_id)
            .order_by(ExecutionJobORM.created_at.desc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]

    async def list_stale(
        self, *, older_than: datetime, limit: int = 100
    ) -> Sequence[ExecutionJob]:
        result = await self.session.execute(
            select(ExecutionJobORM)
            .where(
                ExecutionJobORM.status.in_(["sent", "submitted"]),
                ExecutionJobORM.created_at < older_than,
            )
            .order_by(ExecutionJobORM.created_at.asc())
            .limit(limit)
        )
        return [self._orm_to_schema(o) for o in result.scalars().all()]
