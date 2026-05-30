# Mocking Guidelines

## Mock at System Boundaries Only

Mock external dependencies your code talks to across a network or process boundary: HTTP APIs, databases, filesystems, external services. Everything else should be real.

| Mock this | Don't mock this |
|---|---|
| `httpx.AsyncClient` (Piston API, NIM AI) | `CodeWrapper`, `ExecutionResultFormatter` |
| Filesystem reads/writes | `StaticCodeValidator` |
| External process calls | Suite runner builders |

---

## Good: Mock `httpx.AsyncClient` (External API)

```python
# backend/tests/unit/test_piston_service.py:29-136
class TestPistonServiceExecute:
    async def test_execute_code_success(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "run": {"stdout": "Hello\n", "stderr": "", "code": 0, "wall_time": 0.05},
                "language": "python", "version": "3.10.0",
            }
            mock_instance.post.return_value = mock_response

            service = PistonService()
            result = await service.execute("python", 'print("Hello")')
            assert result.stdout == "Hello\n"
```

Mocks `httpx.AsyncClient` at the module import level — the exact point where `PistonService` reaches out to the Docker sandbox. The entire `PistonService` runs with real logic: code wrapping, result formatting, validation.

**Test survives:** extracting `CodeWrapper` to `adapters/code_wrappers/`, renaming `ExecutionResultFormatter`, inlining static validation.

## Don't Mock Extracted Classes

After extracting `CodeWrapper`, `ExecutionResultFormatter`, or suite runners, DO NOT mock them in tests for the code that uses them. They are in-process collaborators — use the real implementation.

```python
# DON'T — mocks an in-process collaborator
with patch("app.services.piston_service.get_wrapper") as mock_get:
    mock_get.return_value = PythonCodeWrapper()
    result = await service.execute("python", code)
    # This test is now coupled to the extraction artifact
```

```python
# DO — use the real collaborator
service = PistonService()
result = await service.execute("python", code)
# Real get_wrapper() resolves the real PythonCodeWrapper
```

Why: Mocking in-process collaborators means you're testing the mock setup, not the integration. If `get_wrapper` changes its dispatch logic, the real-service test catches it; the mocked test is silent.

---

## Good: Mock Through FastAPI Dependency Overrides

```python
# backend/tests/integration/test_submit_endpoints.py
app.dependency_overrides[get_repository] = lambda: mock_question_repo
app.dependency_overrides[get_executor] = lambda: mock_executor
```

Use the framework's native injection point. This is cleaner than `patch.object` because it's the same mechanism production uses — just with a different implementation at test time.

---

## Prefer Fakes Over Mocks for In-Process Dependencies

A fake is a lightweight implementation of an interface. It's more robust than a mock because it exercises the real contract.

```python
class FakeExecutor:
    async def execute(self, language, code, stdin="", version=None):
        if "error" in code.lower():
            return ExecutionResult(stderr="SyntaxError", exit_code=1)
        return ExecutionResult(stdout=stdin + "\n", exit_code=0)
```

Use this instead of `AsyncMock` with return values when the fake is simple enough.

---

## Warning Signs

- Mocking a class or function you just extracted
- Patching at `app.services.piston_service.xxx` instead of using the real thing
- More mock setup code than test logic
- Tests that fail after an internal rename with no behavior change
- `from ... import ...` of a private function or method (starts with `_`)
