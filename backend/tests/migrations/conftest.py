"""Fixtures for migration tests.

Migration testing runs against the shared per-suite test schema
(`codecoach_test`) that the parent tests/conftest.py already resets at session
start. The migration module drops all tables itself before exercising the
Alembic graph, so it never depends on `Base.metadata.create_all` to build the
schema — verifying the migrations produce it end-to-end.

In CI this suite runs as its own job against a dedicated, empty
`POSTGRES_DB=codecoach_test`, so there is no cross-suite interference.
"""

import os
import urllib.parse
from pathlib import Path
from typing import Iterator

import pytest
from alembic.config import Config


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


def _is_postgres(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgresql+")


def _migration_url() -> str:
    base = os.environ.get(
        "DATABASE_URL",
        "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach_test",
    ).replace("host.docker.internal", "127.0.0.1")
    if not _is_postgres(base):
        raise RuntimeError(
            f"Unsupported DATABASE_URL for migrations: {base} "
            "(Supabase/PostgreSQL only)"
        )
    # alembic/env.py drives migrations through an async engine, so force the
    # asyncpg driver (same as the app) for the migration runs.
    if not base.startswith("postgresql+asyncpg://"):
        base = base.replace("postgresql://", "postgresql+asyncpg://", 1)
    return base


def _connection_params(url: str):
    normalized = url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urllib.parse.urlparse(normalized)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": urllib.parse.unquote(parsed.username or ""),
        "password": urllib.parse.unquote(parsed.password or ""),
        "database": (parsed.path or "").lstrip("/").split("?")[0] or None,
    }


def _drop_all_tables(url: str) -> None:
    import psycopg

    params = _connection_params(url)
    conn = psycopg.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        dbname=params["database"],
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
            cur.execute("CREATE SCHEMA public")
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def _reset_tables() -> Iterator[None]:
    _drop_all_tables(_migration_url())
    yield


@pytest.fixture(scope="session")
def migration_url() -> str:
    return _migration_url()


@pytest.fixture(scope="session")
def alembic_config(migration_url: str) -> Iterator[Config]:
    """Alembic Config bound to the migration schema.

    DATABASE_URL is pinned to the migration schema for the session so env.py
    (which re-reads the env var at command time) targets the right schema.
    """
    old_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = migration_url
    try:
        cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        cfg.set_main_option("sqlalchemy.url", migration_url)
        yield cfg
    finally:
        if old_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old_url
