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
    from app.models.orm import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
