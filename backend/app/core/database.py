from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from app.core.config import get_settings, is_production

settings = get_settings()

# NullPool in testing avoids cross-event-loop connection reuse (FastAPI sync
# TestClient + async tests run on different loops, which poisons pooled
# connections). Production uses the default pooled engine.
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool if not is_production() else None,
    pool_pre_ping=True,
)
async_session_maker: async_sessionmaker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Create tables if missing.

    MySQL can transiently return errors 1684/1824 ("table skipped, DDL in
    flight") when `create_all` reflects table metadata right after schema
    churn (e.g. CI test runs dropping/recreating tables). Retry with a bounded
    backoff so a DDL race never takes the service down at startup.
    """
    import asyncio
    import logging

    from app.models.orm import Base

    logger = logging.getLogger(__name__)

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    for attempt in range(1, 5):
        try:
            await _create()
            return
        except Exception as exc:  # noqa: BLE001 - transient DDL race is broad
            if "1684" in str(exc) or "1824" in str(exc):
                logger.warning(
                    "init_db hit transient DDL race (%s), retrying (%d/4)",
                    exc.__class__.__name__,
                    attempt,
                )
                await asyncio.sleep(0.4 * attempt)
                continue
            raise
    raise RuntimeError("init_db failed after 4 attempts due to persistent DDL race")
