"""
Test configuration and fixtures for CodeCoach AI API testing.
"""

import os

# Set safe defaults BEFORE app.main is imported so that Settings() does not
# fail-fast at collection time (ENVIRONMENT unset = production = requires a
# JWT secret). Individual tests override via monkeypatch/test_env_vars.
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!!")

import re  # noqa: E402
import urllib.parse  # noqa: E402
import asyncio  # noqa: E402

_TEST_DB = "codecoach_test"

# Under pytest-xdist each worker process imports this module and resets the
# schema; give every worker its own schema so parallel runs never race on the
# same `codecoach_test` object (e.g. gw0 -> codecoach_test_gw0).
_xdist_worker = os.environ.get("PYTEST_XDIST_WORKER")
if _xdist_worker:
    _TEST_DB = f"{_TEST_DB}_{_xdist_worker}"


def _is_mysql_url(url: str) -> bool:
    return url.startswith("mysql+aiomysql://") or url.startswith("mysql://")


def _strip_pgbouncer(url: str) -> str:
    """Drop the Supabase transaction-pooler `?pgbouncer=true` param.

    asyncpg / SQLAlchemy would otherwise forward `pgbouncer` as an unknown
    connection kwarg. Schema tooling talks to the session pooler directly, so
    the param is meaningless here.
    """
    if "pgbouncer" not in url:
        return url
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    params = [
        kv
        for kv in (query.split("&") if query else [])
        if not kv.startswith("pgbouncer")
    ]
    return urllib.parse.urlunsplit((scheme, netloc, path, "&".join(params), fragment))


def _ensure_test_database() -> str:
    """Route tests to a dedicated `codecoach_test` schema.

    MySQL: creates the `codecoach_test` database next to the app database.
    PostgreSQL/Supabase: uses a dedicated `codecoach_test` schema on the same
    server (Supabase exposes a single database, so schema isolation is used).

    Runs at import time so Settings() picks it up before app.main is loaded.
    """
    from urllib.parse import urlparse

    import pymysql
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())

    base_url = os.environ.get(
        "DATABASE_URL",
        "mysql+aiomysql://codecoach:codecoach@127.0.0.1:3306/codecoach",
    )
    # When running on the host (not inside Docker), reach MySQL via localhost.
    base_url = base_url.replace("host.docker.internal", "127.0.0.1")
    if not _is_mysql_url(base_url):
        return _ensure_postgres_test_schema(base_url)

    match = re.match(r"^(mysql\+aiomysql://[^/]+)/(?:[^?]*)(\?.*)?$", base_url)
    if not match:
        raise RuntimeError(f"Unsupported DATABASE_URL for tests: {base_url}")
    test_url = f"{match.group(1)}/{_TEST_DB}{match.group(2) or ''}"
    os.environ["DATABASE_URL"] = test_url

    parsed = urlparse(test_url.replace("mysql+aiomysql://", "mysql://"))
    conn = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=urllib.parse.unquote(parsed.username or ""),
        password=urllib.parse.unquote(parsed.password or ""),
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS {_TEST_DB} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE {_TEST_DB}")
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            for table in (
                "rate_limit_events",
                "course_progress",
                "lessons",
                "modules",
                "courses",
                "questions",
                "user_daily_usage",
                "user_usage_events",
                "users",
                "feature_flags",
                "audit_logs",
                "generation_jobs",
            ):
                cur.execute(f"DROP TABLE IF EXISTS {table}")
            cur.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    finally:
        conn.close()

    # Create schema so API tests (ASGITransport does not run lifespan) see tables.
    _create_schema_sync(test_url)
    return test_url


def _ensure_postgres_test_schema(base_url: str) -> str:
    """Point DATABASE_URL at a dedicated `codecoach_test` schema.

    The Prisma schema and app metadata are recreated on that schema, and
    `search_path` is set via the connection so every app query targets it.
    """
    import asyncpg

    base_url = _strip_pgbouncer(base_url)

    async def _setup() -> None:
        conn = await asyncpg.connect(base_url)
        try:
            await conn.execute(f'DROP SCHEMA IF EXISTS "{_TEST_DB}" CASCADE')
            await conn.execute(f'CREATE SCHEMA "{_TEST_DB}"')
        finally:
            await conn.close()

    asyncio.run(_setup())

    os.environ["DATABASE_URL"] = base_url
    os.environ["DATABASE_SEARCH_PATH"] = _TEST_DB

    # Rebuild from a clean slate so leftover migration-only tables never
    # conflict, retrying transient network/DDL errors.
    import time as _time

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base

    async def _create_schema_async() -> None:
        engine = create_async_engine(
            base_url.replace("postgresql://", "postgresql+asyncpg://", 1),
            poolclass=NullPool,
            connect_args={
                "server_settings": {"search_path": _TEST_DB},
                # Supabase poolers reuse prepared-statement names across
                # connections; disable asyncpg's statement cache so
                # `create_all` does not hit DuplicatePreparedStatementError.
                "statement_cache_size": 0,
            },
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    for _attempt in range(1, 6):
        try:
            asyncio.run(_create_schema_async())
            break
        except Exception:  # noqa: BLE001 - transient DDL/network race is broad
            if _attempt == 5:
                raise
            _time.sleep(0.5 * _attempt)
    return base_url


def _create_schema_sync(test_url: str) -> None:
    """Create the app schema from metadata (used by the MySQL path)."""
    import time as _time

    from sqlalchemy import create_engine, text
    from app.models.orm import Base

    sync_url = test_url.replace("mysql+aiomysql://", "mysql+pymysql://")
    for _attempt in range(1, 6):
        engine = create_engine(sync_url)
        try:
            with engine.connect() as conn:
                conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                Base.metadata.drop_all(conn)
                conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
            Base.metadata.create_all(engine)
            engine.dispose()
            break
        except Exception:  # noqa: BLE001 - transient 1684/1824 DDL race
            engine.dispose()
            if _attempt == 5:
                raise
            _time.sleep(0.5 * _attempt)


_ensure_test_database()

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from typing import Generator, AsyncGenerator  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

from app.main import app  # noqa: E402
from app.services.question_bank import QuestionBank  # noqa: E402


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Create a test client for synchronous testing."""
    with TestClient(app) as client:
        yield client


def _test_engine_kwargs() -> dict:
    """Shared engine kwargs: force asyncpg driver + test search_path."""
    kwargs = {}
    db_url = os.environ["DATABASE_URL"]
    if db_url.startswith("postgresql://"):
        kwargs["connect_args"] = {
            "server_settings": {"search_path": os.environ["DATABASE_SEARCH_PATH"]},
            # Supabase poolers reuse prepared-statement names across
            # connections; disable asyncpg's statement cache so DDL / DML does
            # not hit DuplicatePreparedStatementError.
            "statement_cache_size": 0,
        }
    return kwargs


def _test_db_url() -> str:
    """Return the test DATABASE_URL with the asyncpg driver forced."""
    db_url = _strip_pgbouncer(os.environ["DATABASE_URL"])
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return db_url


async def _seed_questions() -> int:
    """Seed the sample question bank into the test database if empty.

    The file-based question repository used to load sample_questions.json
    automatically; with a DB-backed bank the test database starts empty, so
    the same questions are seeded for API/integration tests. Unit SQL
    repository tests clean tables (test_db) for isolation.
    """
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base, QuestionORM

    engine = create_async_engine(
        _test_db_url(), poolclass=NullPool, **_test_engine_kwargs()
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    questions_path = (
        Path(__file__).resolve().parent.parent / "questions" / "sample_questions.json"
    )
    count = 0
    if questions_path.exists():
        with open(questions_path, encoding="utf-8") as f:
            data = json.load(f)
        questions = data.get("questions", data) if isinstance(data, dict) else data

        async with async_session() as session:
            from sqlalchemy import select

            existing = (await session.execute(select(QuestionORM.id))).scalars().all()
            if not existing:
                from app.models.schemas import Question

                for item in questions:
                    try:
                        q = Question(**item)
                    except Exception:
                        continue
                    session.add(
                        QuestionORM(
                            id=q.id,
                            title=q.title,
                            difficulty=q.difficulty.value,
                            category=q.category,
                            company_tags=q.company_tags,
                            description=q.description,
                            starter_code=q.starter.model_dump()
                            if hasattr(q.starter, "model_dump")
                            else q.starter,
                            examples=[
                                e.model_dump() if hasattr(e, "model_dump") else e
                                for e in q.examples
                            ],
                            test_cases=[
                                tc.model_dump() if hasattr(tc, "model_dump") else tc
                                for tc in q.test_cases
                            ],
                            hints=q.hints,
                            solution=q.solution,
                            time_complexity=q.time_complexity,
                            space_complexity=q.space_complexity,
                            constraints=q.constraints,
                            is_interactive=1 if q.is_interactive else 0,
                        )
                    )
                    count += 1
                await session.commit()
    await engine.dispose()
    return count


def _seed_questions_sync() -> int:
    """Sync variant of _seed_questions (only safe outside a running loop)."""
    return asyncio.run(_seed_questions())


@pytest.fixture(scope="session", autouse=True)
def seed_test_questions():
    """Seed the sample question bank once per session.

    Sync fixture using ``asyncio.run`` so it never depends on the (function-
    scoped) pytest-asyncio event loop, avoiding ScopeMismatch when the app
    itself spins up its own loop.
    """
    _seed_questions_sync()
    yield


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous testing."""
    await _seed_questions()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_db():
    """Provide an isolated DB-backed session for SQL repository tests.

    Cleans all tables before each test so tests do not interfere with each
    other or with the running application's database. Works on both MySQL and
    PostgreSQL/Supabase (search_path points at the `codecoach_test` schema).
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base

    db_url = _test_db_url()
    test_engine = create_async_engine(
        db_url, poolclass=NullPool, **_test_engine_kwargs()
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DELETE FROM {table.name}"))
            if hasattr(table.c, "id") and db_url.startswith("postgresql+asyncpg"):
                await conn.execute(
                    text(f"ALTER SEQUENCE IF EXISTS {table.name}_id_seq RESTART WITH 1")
                )

    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await test_engine.dispose()
    await _seed_questions()


@pytest.fixture
def mock_piston_service():
    """Mock Piston service for testing."""

    class MockPistonService:
        async def execute(
            self, language: str, code: str, stdin: str = "", version: str = None
        ):
            """Mock execution returning ExecutionResult."""
            from app.ports.code_executor import ExecutionResult

            if "error" in code.lower():
                return ExecutionResult(
                    exit_code=1, stderr="SyntaxError: invalid syntax"
                )
            return ExecutionResult(stdout="Hello, World!\n", exit_code=0)

        def validate_code(self, language: str, code: str):
            """Mock code validation."""
            is_valid = "error" not in code.lower()
            return {
                "valid": is_valid,
                "warnings": ["Consider adding type hints"]
                if language == "python"
                else [],
                "errors": ["Syntax error on line 1"] if not is_valid else [],
            }

        async def get_runtimes(self):
            """Mock runtime information."""
            return [
                {
                    "language": "python",
                    "version": "3.11.0",
                    "aliases": ["py", "python3"],
                    "runtime": "cpython",
                }
            ]

    return MockPistonService


@pytest.fixture
def mock_question_bank():
    """Mock QuestionBank for testing."""
    from unittest.mock import AsyncMock

    bank = AsyncMock(spec=QuestionBank)
    return bank


@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    env_vars = {
        "GROQ_API_KEY": "test_groq_key",
        "PISTON_API_URL": "https://emkc.org/api/v2/piston",
        "QUESTIONS_FILE_PATH": "tests/fixtures/test_questions.json",
        "RATE_LIMIT_PER_MINUTE": "100",
        "RATE_LIMIT_PER_HOUR": "1000",
        "ENVIRONMENT": "testing",
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only-32chars!!",
        "COACH_RATE_LIMIT": "1000/minute",
        "RUN_RATE_LIMIT": "1000/minute",
    }

    # Store original values
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def admin_headers(test_client: TestClient) -> dict:
    """Return Authorization headers for an admin user.

    Registers (or logs in) a fixed admin user and promotes it to admin by
    updating the users table directly, mirroring test_admin_curriculum_crud.py.
    """
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": "auditadmin",
            "email": "auditadmin@test.com",
            "password": "testpass123",
        },
    )
    if res.status_code != 201:
        res = test_client.post(
            "/api/auth/login",
            json={"username": "auditadmin", "password": "testpass123"},
        )
    token = res.json()["access_token"]

    async def _promote_admin() -> None:
        from sqlalchemy import text as sa_text
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy.pool import NullPool

        engine = create_async_engine(
            _test_db_url(), poolclass=NullPool, **_test_engine_kwargs()
        )
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            await session.execute(
                sa_text("UPDATE users SET role='admin' WHERE username=:u"),
                {"u": "auditadmin"},
            )
            await session.commit()
        await engine.dispose()

    asyncio.run(_promote_admin())

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_question_data():
    """Provide sample question data for testing."""
    return {
        "id": "test-question",
        "title": "Test Question",
        "difficulty": "easy",
        "category": "arrays",
        "company_tags": ["TestCompany"],
        "description": "This is a test question for unit testing.",
        "starter": {"python": "def test_function(input):\n    pass"},
        "examples": [
            {
                "input": "input = [1, 2, 3]",
                "output": "6",
                "explanation": "Sum of array elements",
            }
        ],
        "test_cases": [
            {
                "input": "[1, 2, 3]",
                "expected_output": "6",
                "description": "Basic test case",
                "hidden": False,
            }
        ],
        "hints": ["Consider using a loop", "Think about edge cases"],
        "solution": "Use a simple loop to sum the elements",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "constraints": ["1 <= len(array) <= 1000", "-1000 <= array[i] <= 1000"],
    }


@pytest.fixture
def sample_coaching_request():
    """Provide sample coaching request data."""
    return {
        "problem": "Given an array of integers, find the maximum sum of any contiguous subarray.",
        "code": "def max_subarray_sum(nums):\n    max_sum = nums[0]\n    current_sum = nums[0]\n    \n    for i in range(1, len(nums)):\n        current_sum = max(nums[i], current_sum + nums[i])\n        max_sum = max(max_sum, current_sum)\n    \n    return max_sum",
        "language": "python",
        "message": "Can you review my solution and suggest improvements?",
        "mode": "review",
        "difficulty": "medium",
    }


@pytest.fixture
def sample_code_execution_request():
    """Provide sample code execution request data."""
    return {
        "language": "python",
        "code": "print('Hello, World!')\nprint(sum([1, 2, 3, 4, 5]))",
        "stdin": "",
        "version": "3.11.0",
    }


@pytest.fixture
def temp_questions_file():
    """Create a temporary questions file for testing."""
    test_questions = [
        {
            "id": "test-question-1",
            "title": "Test Question 1",
            "difficulty": "easy",
            "category": "arrays",
            "company_tags": ["TestCompany"],
            "description": "Test description 1",
            "starter": {"python": "def test1(input):\n    pass"},
            "examples": [{"input": "[1,2,3]", "output": "6", "explanation": "Sum"}],
            "test_cases": [
                {"input": "[1,2,3]", "expected_output": "6", "description": "Test"}
            ],
        },
        {
            "id": "test-question-2",
            "title": "Test Question 2",
            "difficulty": "medium",
            "category": "strings",
            "company_tags": ["AnotherCompany"],
            "description": "Test description 2",
            "starter": {"python": "def test2(input):\n    pass"},
            "examples": [
                {"input": "'hello'", "output": "'olleh'", "explanation": "Reverse"}
            ],
            "test_cases": [
                {
                    "input": "'hello'",
                    "expected_output": "'olleh'",
                    "description": "Test",
                }
            ],
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_questions, f, indent=2)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)
