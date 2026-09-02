from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool
from app.core.config import get_settings
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
# Must apply in production as well — Supabase transaction pooler (pgbouncer)
# is used in production and does not support prepared statements.
if _db_url.startswith("postgresql"):
    _connect_args.setdefault("connect_args", {}).update(pooler_connect_args())

# NullPool only for isolated test schemas (DATABASE_SEARCH_PATH). In dev
# it forces a new TLS handshake to Supabase per-request (~5s), which is
# the "Request Timeouts" seen in the UI. Pooled engine reuses connections.
# Pool tuning args are only valid for pooled engines — NullPool rejects
# pool_size / max_overflow / pool_timeout.
_use_nullpool = bool(settings.DATABASE_SEARCH_PATH)
_pool_kwargs: dict = {}
if not _use_nullpool:
    _pool_kwargs = dict(
        pool_size=20, max_overflow=10, pool_timeout=30, pool_recycle=300
    )

engine: AsyncEngine = create_async_engine(
    _db_url,
    poolclass=NullPool if _use_nullpool else None,
    pool_pre_ping=True,
    **_pool_kwargs,
    **_connect_args,
)
async_session_maker: async_sessionmaker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
