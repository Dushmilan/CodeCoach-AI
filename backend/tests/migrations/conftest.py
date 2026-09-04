"""Fixtures for migration tests.

Migration testing runs against the schema named by DATABASE_SEARCH_PATH
(default ``public``) on the configured server. The harness resets that
schema itself before exercising the Alembic graph, so it never depends on
``Base.metadata.create_all`` to build the schema — verifying the migrations
produce it end-to-end. alembic/env.py reads the same env var, so reset,
migrate, and version reads all target one schema.

In CI this suite runs as its own job against a dedicated, empty
``POSTGRES_DB=codecoach_test``, so there is no cross-suite interference.
"""

import os
import re
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


def _target_schema() -> str:
    """Schema under test: DATABASE_SEARCH_PATH, defaulting to public."""
    schema = os.environ.get("DATABASE_SEARCH_PATH", "public")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise RuntimeError(f"Unsafe DATABASE_SEARCH_PATH for migrations: {schema!r}")
    return schema


def _drop_all_tables(url: str, schema: str) -> None:
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
            cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            cur.execute(f'CREATE SCHEMA "{schema}"')
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def _reset_tables() -> Iterator[None]:
    """Reset the migration schema once per session.

    Migration tests chain DB state across the file (each test starts from
    the head left by the previous one), so the reset must stay
    session-scoped — a per-test reset would strand downgrade targets.
    """
    _drop_all_tables(_migration_url(), _target_schema())
    yield


@pytest.fixture(scope="session", autouse=True)
def seed_test_questions():
    """Neutralize the parent conftest's question seed.

    The seed recreates tables via ``create_all`` and inserts rows; run after
    the reset it would rebuild tables Alembic is about to create (spurious
    DuplicateTable), and migration tests never need seed data. Shadowing the
    parent fixture keeps DDL tests hermetic regardless of fixture order.
    """
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
