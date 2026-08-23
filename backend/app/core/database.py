from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from app.core.config import get_settings, is_production
from app.core.db_url import pooler_connect_args, strip_pgbouncer

settings = get_settings()

# Supabase transaction-pooler URLs carry a `?pgbouncer=true` param that
# asyncpg/SQLAlchemy treat as an unknown connection option; drop it and keep
# the rest of the query string (e.g. sslmode).
_db_url = strip_pgbouncer(settings.DATABASE_URL)

# NullPool in testing avoids cross-event-loop connection reuse (FastAPI sync
# TestClient + async tests run on different loops, which poisons pooled
# connections). Production uses the default pooled engine.
_connect_args: dict = {}
if settings.DATABASE_SEARCH_PATH:
    # Tests route queries to a dedicated schema via Postgres search_path.
    _connect_args["connect_args"] = {
        "server_settings": {"search_path": settings.DATABASE_SEARCH_PATH}
    }

# Supabase poolers reuse prepared-statement names across connections; disable
# asyncpg's statement cache so DDL / DML does not hit
# DuplicatePreparedStatementError (mirrors tests/conftest.py).
if not is_production() and _db_url.startswith("postgresql"):
    _connect_args.setdefault("connect_args", {}).update(pooler_connect_args())

engine: AsyncEngine = create_async_engine(
    _db_url,
    poolclass=NullPool if not is_production() else None,
    pool_pre_ping=True,
    **_connect_args,
)
async_session_maker: async_sessionmaker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
