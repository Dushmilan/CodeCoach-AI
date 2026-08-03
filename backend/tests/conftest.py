"""
Test configuration and fixtures for CodeCoach AI API testing.
"""

import os

# Set safe defaults BEFORE app.main is imported so that Settings() does not
# fail-fast at collection time (ENVIRONMENT unset = production = requires a
# JWT secret). Individual tests override via monkeypatch/test_env_vars.
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!!")
os.environ.setdefault("USE_DATABASE", "false")

import pytest
import pytest_asyncio
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import json
import os
import tempfile

from app.main import app
from app.services.question_bank import QuestionBank


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


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


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
    editing the users file directly, mirroring test_admin_curriculum_crud.py.
    """
    users_path = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")

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

    if os.path.exists(users_path):
        with open(users_path) as f:
            users = json.load(f)
        for u in users:
            if u.get("username") == "auditadmin":
                u["role"] = "admin"
                break
        with open(users_path, "w") as f:
            json.dump(users, f, indent=2)

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
