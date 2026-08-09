"""
Contract tests: verify API responses conform to the OpenAPI contract.

Two layers:

1. Schema integrity — the OpenAPI document is internally consistent: every
   route documents at least one response, response models reference existing
   components, and operationIds are unique.

2. Response contracts — for each route, a representative call (with external
   dependencies overridden by a test double) must return a response that
   validates against the response schema declared in the OpenAPI document.

These tests never touch real external services or the live database; they
prove the *shape* of the API is stable and self-consistent.
"""

from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft7Validator, FormatChecker

from app.main import app


# ---------------------------------------------------------------------------
# OpenAPI schema helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def openapi_schema() -> Dict[str, Any]:
    return app.openapi()


def _resolve_ref(
    schema: Dict[str, Any],
    full: Dict[str, Any],
    _seen: Optional[set] = None,
) -> Dict[str, Any]:
    """Recursively resolve all $ref pointers against the OpenAPI components.

    `_seen` guards against circular component references (a self-referencing
    schema) so a pathological OpenAPI document cannot cause unbounded
    recursion.
    """
    if _seen is None:
        _seen = set()
    if isinstance(schema, list):
        return [_resolve_ref(item, full, _seen) for item in schema]
    if not isinstance(schema, dict):
        return schema
    out: Dict[str, Any] = {}
    for key, value in schema.items():
        if key == "$ref" and isinstance(value, str):
            if value.startswith("#/components/schemas/"):
                name = value.split("/")[-1]
                if name in _seen:
                    return {"$ref": value}  # keep the pointer; break the cycle
                _seen.add(name)
                return _resolve_ref(full["components"]["schemas"][name], full, _seen)
            continue
        out[key] = _resolve_ref(value, full, _seen)
    return out


def _make_validator(schema: Dict[str, Any], full: Dict[str, Any]):
    """Build a Draft7 validator with all $refs inlined (no registry needed)."""
    resolved = _resolve_ref(schema, full)
    return Draft7Validator(resolved, format_checker=FormatChecker())


def _response_schema(
    path: str, method: str, status: int, full: Dict[str, Any]
) -> Dict[str, Any]:
    """Return the resolved response content schema for a route+status."""
    op = full["paths"][path][method]
    responses = op.get("responses", {})
    if str(status) not in responses:
        return None
    content = responses[str(status)].get("content", {})
    if "application/json" not in content:
        return None
    return content["application/json"]["schema"]


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _StubQuestionBank:
    """QuestionBank double returning schema-shaped fixtures."""

    async def query(self, filters=None):
        from app.services.question_bank import QuestionPage

        return QuestionPage(
            items=[
                {
                    "id": "q-1",
                    "title": "Two Sum",
                    "difficulty": "easy",
                    "category": "arrays",
                    "company_tags": ["Google"],
                    "description": "Find indices summing to target.",
                    "starter": {"python": "def two_sum(nums, target):\n    pass"},
                    "examples": [
                        {
                            "input": "[2,7,11,15], 9",
                            "output": "[0,1]",
                            "explanation": "nums[0]+nums[1]=9",
                        }
                    ],
                    "test_cases": [
                        {
                            "input": "[2,7,11,15], 9",
                            "expected_output": "[0,1]",
                            "description": "Basic case",
                            "hidden": False,
                        }
                    ],
                    "hints": ["Use a hash map."],
                    "solution": "Hash map lookup.",
                    "time_complexity": "O(n)",
                    "space_complexity": "O(n)",
                    "constraints": ["2 <= len(nums)"],
                }
            ],
            total=1,
            page=1,
            per_page=100,
        )

    async def stats(self):
        from app.services.question_bank import QuestionStats

        return QuestionStats(
            total=1,
            difficulty_counts={"easy": 1, "medium": 0, "hard": 0},
            category_counts={"arrays": 1},
            categories=["arrays", "strings"],
            companies=["Google"],
        )

    async def companies(self):
        return {"companies": ["Google"]}


def _install_overrides(overrides: Dict[Any, Any]):
    for key, value in overrides.items():
        app.dependency_overrides[key] = value


def _clear_overrides(keys: Any):
    for key in keys:
        app.dependency_overrides.pop(key, None)


@pytest.fixture
def auth_and_deps():
    """Override auth + external-service dependencies for contract calls."""
    from app.api.auth_deps import get_current_user
    from app.api.dependencies import get_question_bank
    from app.api.coach import get_coaching_provider
    from app.api.dependencies import get_executor
    from app.models.auth_schemas import UserResponse
    from tests.fixtures.mock_coaching_provider import MockCoachingProvider

    async def override_get_current_user():
        return UserResponse(
            id="contract-user",
            username="contractuser",
            email="contract@test.com",
            is_active=True,
            plan="premium",
            created_at="2025-01-01T00:00:00Z",
        )

    _install_overrides(
        {
            get_current_user: override_get_current_user,
            get_coaching_provider: MockCoachingProvider,
            get_executor: lambda: _ExecutorStub(),
            get_question_bank: lambda: _StubQuestionBank(),
        }
    )
    try:
        yield
    finally:
        _clear_overrides(
            [get_current_user, get_coaching_provider, get_executor, get_question_bank]
        )


class _ExecutorStub:
    async def execute(self, language, code, stdin="", version=None):
        from app.ports.code_executor import ExecutionResult

        return ExecutionResult(stdout="Hello, World!\n", exit_code=0)

    def validate_code(self, language, code):
        return {"valid": True, "warnings": [], "errors": []}

    async def get_runtimes(self):
        return [
            {
                "language": "python",
                "version": "3.11.0",
                "aliases": ["py"],
                "runtime": "cpython",
            }
        ]


# ---------------------------------------------------------------------------
# Layer 1: OpenAPI schema integrity
# ---------------------------------------------------------------------------


def test_every_route_documents_a_response(openapi_schema):
    missing = []
    for path, methods in openapi_schema["paths"].items():
        for method, op in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            responses = op.get("responses", {})
            if not responses:
                missing.append(f"{method.upper()} {path}")
    assert not missing, f"Routes missing response documentation: {missing}"


def test_response_schema_refs_resolve(openapi_schema):
    unresolved = []
    for path, methods in openapi_schema["paths"].items():
        for method, op in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            for status, resp in op.get("responses", {}).items():
                for media in resp.get("content", {}).values():
                    schema = media.get("schema", {})
                    if schema.get("$ref", "").startswith("#/components/schemas/"):
                        name = schema["$ref"].split("/")[-1]
                        if name not in openapi_schema["components"]["schemas"]:
                            unresolved.append(
                                f"{method.upper()} {path} {status}: {name}"
                            )
    assert not unresolved, f"Unresolvable response schema refs: {unresolved}"


def test_operation_ids_are_unique(openapi_schema):
    seen: Dict[str, str] = {}
    duplicates = []
    for path, methods in openapi_schema["paths"].items():
        for method, op in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            op_id = op.get("operationId")
            if op_id:
                if op_id in seen:
                    duplicates.append(op_id)
                seen[op_id] = f"{method.upper()} {path}"
    assert not duplicates, f"Duplicate operationIds: {duplicates}"


# ---------------------------------------------------------------------------
# Layer 2: Response contracts
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _validate_response(
    client, method, path, openapi_schema, status, json_kwargs=None, headers=None
):
    """Call route and validate the response against its declared schema."""
    response = client.request(
        method.upper(), path, json=json_kwargs, headers=headers or {}
    )
    schema = _response_schema(
        path, method.lower(), response.status_code, openapi_schema
    )
    if response.status_code != status:
        return response, schema, f"expected {status}, got {response.status_code}"

    if schema is None:
        return response, None, None
    resolved = _resolve_ref(schema, openapi_schema)
    validator = _make_validator(resolved, openapi_schema)
    errors = list(validator.iter_errors(response.json()))
    return response, schema, errors


@pytest.mark.usefixtures("auth_and_deps")
class TestResponseContracts:
    def test_health_ok(self, client, openapi_schema):
        response, _, errors = _validate_response(
            client, "GET", "/health/", openapi_schema, 200
        )
        assert errors is None or not errors, errors
        assert response.status_code == 200

    def test_questions_list(self, client, openapi_schema):
        response, _, errors = _validate_response(
            client, "GET", "/api/questions/", openapi_schema, 200
        )
        assert errors is None or not errors, errors
        assert response.status_code == 200

    def test_questions_categories(self, client, openapi_schema):
        response, _, errors = _validate_response(
            client, "GET", "/api/questions/categories", openapi_schema, 200
        )
        assert response.status_code == 200

    def test_questions_companies(self, client, openapi_schema):
        response, _, errors = _validate_response(
            client, "GET", "/api/questions/companies", openapi_schema, 200
        )
        assert response.status_code == 200

    def test_coach_modes(self, client, openapi_schema):
        response, _, errors = _validate_response(
            client, "GET", "/api/coach/modes", openapi_schema, 200
        )
        assert response.status_code == 200

    def test_coach_languages(self, client, openapi_schema):
        response, _, errors = _validate_response(
            client, "GET", "/api/coach/languages", openapi_schema, 200
        )
        assert response.status_code == 200
