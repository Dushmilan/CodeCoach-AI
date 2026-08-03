"""
Test configuration and fixtures for CodeCoach AI API testing.
"""

import os

# Set safe defaults BEFORE app.main is imported so that Settings() does not
# fail-fast at collection time (ENVIRONMENT unset = production = requires a
# JWT secret). Individual tests override via monkeypatch/test_env_vars.
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!!")

import re
import urllib.parse

_TEST_DB = "codecoach_test"


def _ensure_test_database() -> str:
    """Route tests to a dedicated MySQL `codecoach_test` database.

    Loads credentials from the repository root `.env` (if present) so the
    suite runs against the same MySQL instance as the app. Creates the
    database if it does not exist and returns the test URL. Runs at import
    time so Settings() picks it up before app.main is loaded.
    """
    from urllib.parse import urlparse

    import pymysql
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())

    # When running on the host (not inside Docker), reach Piston via localhost.
    # The repo .env points at the Docker-internal hostname `piston`.
    if "piston" in os.environ.get("PISTON_API_URL", ""):
        os.environ["PISTON_API_URL"] = os.environ["PISTON_API_URL"].replace(
            "piston", "127.0.0.1"
        )

    base_url = os.environ.get(
        "DATABASE_URL",
        "mysql+aiomysql://codecoach:codecoach@127.0.0.1:3306/codecoach",
    )
    # When running on the host (not inside Docker), reach MySQL via localhost.
    base_url = base_url.replace("host.docker.internal", "127.0.0.1")
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
            for table in (
                "course_progress",
                "lessons",
                "modules",
                "courses",
                "questions",
                "users",
                "feature_flags",
                "audit_logs",
                "generation_jobs",
            ):
                cur.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
    finally:
        conn.close()

    # Create schema so API tests (ASGITransport does not run lifespan) see tables.
    from sqlalchemy import create_engine
    from app.models.orm import Base

    sync_url = test_url.replace("mysql+aiomysql://", "mysql+pymysql://")
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)
    engine.dispose()
    return test_url


_ensure_test_database()

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
import asyncio  # noqa: E402
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
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Create a test client for synchronous testing."""
    with TestClient(app) as client:
        yield client


async def _seed_questions() -> int:
    """Seed the sample question bank into the MySQL test database if empty.

    The file-based question repository used to load sample_questions.json
    automatically; with MySQL the test database starts empty, so the same
    questions are seeded for API/integration tests. Unit SQL repository tests
    truncate tables (test_db) for isolation.
    """
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base, QuestionORM

    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
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


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_test_questions():
    """Seed the sample question bank once per session."""
    await _seed_questions()
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
    """Provide an isolated MySQL-backed session for SQL repository tests.

    Truncates all tables before each test so tests do not interfere with
    each other or with the running application's database. Schema is created
    by the app at startup (init_db) and must not be dropped mid-session.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base

    test_engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name}"))
        await conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await test_engine.dispose()
    await _seed_questions()


@pytest.fixture
def mock_nim_service():
    """Mock NIM service for testing."""

    class MockNIMService:
        responses = {
            "hint": "Consider using a hash map to solve this problem.",
            "review": "Your code looks good, but consider edge cases like empty arrays.",
            "explain": "This is a classic problem that requires understanding of data structures.",
            "debug": "The issue appears to be in your loop condition. Check line 5.",
        }

        def __init__(self, api_key: str = "test_key"):
            self.api_key = api_key

        async def get_coaching_response(
            self,
            problem: str,
            code: str,
            language: str,
            message: str,
            mode: str,
            difficulty: str,
            **kwargs,
        ):
            """Mock coaching response generation."""
            yield self.responses.get(mode, "Here's some guidance for your problem.")

        async def get_structured_coaching_response(
            self,
            problem: str,
            code: str,
            language: str,
            message: str,
            mode: str,
            difficulty: str,
            **kwargs,
        ):
            """Mock structured coaching response generation."""
            return {
                "summary": self.responses.get(
                    mode, "Here's some guidance for your problem."
                ),
                "hints": [],
                "code_review": None,
                "complexity_analysis": None,
                "suggestions": [],
                "edge_cases": [],
                "explanation": None,
                "debug_help": None,
            }

    return MockNIMService


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
        "NVIDIA_API_KEY": "test_nvidia_key",
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

    from urllib.parse import urlparse

    import pymysql

    parsed = urlparse(
        os.environ["DATABASE_URL"].replace("mysql+aiomysql://", "mysql://")
    )
    conn = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=urllib.parse.unquote(parsed.username or ""),
        password=urllib.parse.unquote(parsed.password or ""),
        database=os.environ["DATABASE_URL"].rsplit("/", 1)[-1],
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET role='admin' WHERE username=%s", ("auditadmin",)
            )
        conn.commit()
    finally:
        conn.close()

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
