# Tests: Behavior, Not Implementation

Tests should describe *what* the system does, not *how* it does it.

---

## Good: Tests Through Public Interfaces

Test real business logic; mock at system boundaries only (HTTP, filesystem, external APIs).

```python
# backend/tests/unit/test_piston_service.py:333-382
class TestPistonServiceEvaluateSuite:
    async def test_evaluate_suite_mocked_python_runner(self, service):
        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"6\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite(
                "python", "def add(a, b): return a + b",
                [{"input": "2\n4", "expected_output": "6", "hidden": False}],
            )
            assert results[0].passed is True
```

Creates a real `PistonService` with full logic (language validation, runner generation, output parsing). Mocks only `service.execute` — the outermost boundary that would call the external Piston API. Exercises `evaluate_suite()` end-to-end through its public interface.

**Test survives:** renaming `_parse_suite_output`, inlining `_normalize`, extracting suite runners to new modules.

---

## Bad: Tests Coupled to Internals

Testing private methods directly. Breaks on refactor even when behavior is unchanged.

```python
# backend/tests/unit/test_suite_runners.py:287-498
class TestParseSuiteOutput:
    def _parse(self, service, stdout="", stderr="", exit_code=0, signal=None, test_cases=None):
        exec_result = ExecutionResult(
            stdout=stdout, stderr=stderr, exit_code=exit_code, signal=signal
        )
        return service._parse_suite_output(exec_result, test_cases)  # private method!
```

There are already excellent `TestPistonServiceEvaluateSuite` tests exercising the same logic through `evaluate_suite()`. These 18+ `_parse_suite_output` tests bypass the public interface entirely. If `_parse_suite_output` is renamed or inlined, these tests break — even though the public contract is unchanged.

```python
# backend/tests/unit/test_suite_runners.py:447-451
def test_normalize_collapses_whitespace(self, service):
    assert service._normalize("  [1, 2, 3]  ") == "[1,2,3]"
```

`_normalize` is a tiny implementation detail. Its correctness is already verified whenever `evaluate_suite` compares expected vs. actual output. Testing it directly creates brittle coupling with zero marginal value.

**Warning signs:**
- Test calls methods starting with `_`
- Test constructs internal data structures that real callers never pass
- Test breaks after a rename that doesn't change behavior

---

## Good: Mock at Framework Boundaries

Override FastAPI dependencies at the injection point — the cleanest seam in the framework.

```python
# backend/tests/integration/test_submit_endpoints.py:66-94
class TestSubmitEndpoint:
    def test_submit_all_pass(self, test_client, mock_question_repo, mock_executor):
        app.dependency_overrides[get_repository] = lambda: mock_question_repo
        app.dependency_overrides[get_executor] = lambda: mock_executor
        try:
            response = test_client.post("/api/submit/", json={
                "question_id": "test-question",
                "language": "python",
                "code": "print(input())",
            })
            assert response.status_code == 200
            assert data["passed"] is True
        finally:
            app.dependency_overrides.clear()
```

Tests the full request/response cycle — routing, JSON serialization, validation, error handling — through the real FastAPI `TestClient`. Only replaces the outermost dependencies (executor, repository) at FastAPI's native injection point.
