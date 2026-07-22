from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from app.core.config import get_settings

settings = get_settings()

engine: Optional[AsyncEngine] = None
async_session_maker: Optional[async_sessionmaker] = None

if settings.USE_DATABASE:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_URL.startswith("sqlite"),
        poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,
        pool_pre_ping=True,
    )
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )


async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    if not settings.USE_DATABASE:
        yield None
        return
    async with async_session_maker() as session:  # type: ignore[union-attr]
        yield session


async def init_db():
    if not settings.USE_DATABASE:
        return
    from app.models.orm import Base

    async with engine.begin() as conn:  # type: ignore[union-attr]
        await conn.run_sync(Base.metadata.create_all)
