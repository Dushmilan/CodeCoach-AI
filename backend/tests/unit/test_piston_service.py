import httpx
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException


class TestPistonServiceInit:
    def test_default_base_url(self):
        with patch.dict("os.environ", {}, clear=True):
            from app.services.piston_service import PistonService
            service = PistonService()
            assert service.base_url == "http://localhost:2000/api/v2"

    def test_custom_base_url(self):
        with patch.dict("os.environ", {"PISTON_API_URL": "http://piston:2000/api/v2/piston"}):
            from app.services.piston_service import PistonService
            service = PistonService()
            assert service.base_url == "http://piston:2000/api/v2/piston"

    def test_supported_languages(self):
        from app.services.piston_service import PistonService
        service = PistonService()
        assert "python" in service.languages
        assert "javascript" in service.languages
        assert "java" in service.languages
        assert "cpp" in service.languages


class TestPistonServiceExecute:
    @pytest.mark.asyncio
    async def test_execute_code_success(self):
        from app.services.piston_service import PistonService

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
            assert result.exit_code == 0
            assert result.language == "python"

    @pytest.mark.asyncio
    async def test_execute_code_unsupported_language(self):
        from app.services.piston_service import PistonService

        service = PistonService()
        with pytest.raises(HTTPException) as exc:
            await service.execute("brainfuck", "code")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_execute_code_timeout(self):
        from app.services.piston_service import PistonService

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_instance.post.side_effect = httpx.TimeoutException("Timeout")

            service = PistonService()
            with pytest.raises(HTTPException) as exc:
                await service.execute("python", "x")
            assert exc.value.status_code == 504

    @pytest.mark.asyncio
    async def test_execute_code_piston_error(self):
        from app.services.piston_service import PistonService

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Compilation error"
            mock_instance.post.return_value = mock_response

            service = PistonService()
            with pytest.raises(HTTPException) as exc:
                await service.execute("python", "bad code")
            assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_execute_code_with_stdin(self):
        from app.services.piston_service import PistonService

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "run": {"stdout": "hello\n", "stderr": "", "code": 0},
                "language": "python", "version": "3.10.0",
            }
            mock_instance.post.return_value = mock_response

            service = PistonService()
            result = await service.execute("python", "input()", stdin="world")

            assert result.stdout == "hello\n"

    @pytest.mark.asyncio
    async def test_execute_with_custom_version(self):
        from app.services.piston_service import PistonService

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "run": {"stdout": "", "stderr": "", "code": 0},
                "language": "python", "version": "3.10.0",
            }
            mock_instance.post.return_value = mock_response

            service = PistonService()
            result = await service.execute("python", "x", version="3.10.0")
            assert result.language == "python"

    @pytest.mark.asyncio
    async def test_execute_language_c_maps_to_gcc(self):
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "run": {"stdout": "", "stderr": "", "code": 0},
                "language": "c", "version": "10.2.0",
            }
            mock_instance.post.return_value = mock_response

            from app.services.piston_service import PistonService
            service = PistonService()
            result = await service.execute("c", "int main() { return 0; }")
            assert result.language == "c"

    @pytest.mark.asyncio
    async def test_execute_payload_contains_timeout_values(self):
        from app.services.piston_service import PistonService

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "run": {"stdout": "", "stderr": "", "code": 0},
                "language": "python", "version": "3.10.0",
            }
            mock_instance.post.return_value = mock_response

            service = PistonService()
            await service.execute("python", "x")
            payload = mock_instance.post.call_args[1]["json"]
            assert "compile_timeout" in payload
            assert "run_timeout" in payload
            assert payload["compile_timeout"] == 10000
            assert payload["run_timeout"] == 3000

    @pytest.mark.asyncio
    async def test_execute_piston_returns_non_json(self):
        from app.services.piston_service import PistonService
        from fastapi import HTTPException

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("not json")
            mock_response.text = "<html>error</html>"
            mock_instance.post.return_value = mock_response

            service = PistonService()
            with pytest.raises(HTTPException):
                await service.execute("python", "x")

    @pytest.mark.asyncio
    async def test_execute_response_missing_run(self):
        from app.services.piston_service import PistonService

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"language": "python", "version": "3.10.0"}
            mock_instance.post.return_value = mock_response

            service = PistonService()
            result = await service.execute("python", "x")
            assert result.stdout == ""

    @pytest.mark.asyncio
    async def test_execute_piston_connection_error(self):
        from app.services.piston_service import PistonService
        from fastapi import HTTPException

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_instance.post.side_effect = ConnectionError("connection refused")

            service = PistonService()
            with pytest.raises(HTTPException):
                await service.execute("python", "x")


class TestPistonServiceValidate:
    def test_validate_python_code(self):
        from app.services.piston_service import PistonService
        service = PistonService()
        result = service.validate_code("python", 'print("Hello")')
        assert result["valid"] is True

    def test_validate_python_with_input_warning(self):
        from app.services.piston_service import PistonService
        service = PistonService()
        result = service.validate_code("python", 'name = input()')
        assert len(result["warnings"]) > 0

    def test_validate_javascript_code(self):
        from app.services.piston_service import PistonService
        service = PistonService()
        result = service.validate_code("javascript", 'console.log("Hi")')
        assert result["valid"] is True

    def test_validate_java_code(self):
        from app.services.piston_service import PistonService
        service = PistonService()
        result = service.validate_code("java", 'class A { public static void main(String[] a) {} }')
        assert result["valid"] is True

    def test_validate_cpp_code(self):
        from app.services.piston_service import PistonService
        service = PistonService()
        result = service.validate_code("cpp", "int main() { return 0; }")
        assert result["valid"] is True


class TestPistonServiceRuntimes:
    @pytest.mark.asyncio
    async def test_get_runtimes(self):
        from app.services.piston_service import PistonService

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"language": "python", "version": "3.10.0"}]
            mock_instance.get.return_value = mock_response

            service = PistonService()
            runtimes = await service.get_runtimes()

            assert len(runtimes) == 1
            assert runtimes[0]["language"] == "python"

    @pytest.mark.asyncio
    async def test_get_runtimes_non_200(self):
        from app.services.piston_service import PistonService
        from fastapi import HTTPException

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Server Error"
            mock_instance.get.return_value = mock_response

            service = PistonService()
            with pytest.raises(HTTPException):
                await service.get_runtimes()

    @pytest.mark.asyncio
    async def test_get_runtimes_network_error(self):
        from app.services.piston_service import PistonService
        from fastapi import HTTPException

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_client.return_value = mock_instance
            mock_instance.get.side_effect = ConnectionError("network down")

            service = PistonService()
            with pytest.raises(HTTPException):
                await service.get_runtimes()


class TestFileExtension:
    def test_file_extensions(self):
        from app.services.static_code_validator import get_file_extension
        assert get_file_extension("python") == "py"
        assert get_file_extension("javascript") == "js"
        assert get_file_extension("java") == "java"
        assert get_file_extension("cpp") == "cpp"
        assert get_file_extension("unknown") == "txt"
        assert get_file_extension("c") == "c"
        assert get_file_extension("go") == "go"


class TestPistonServiceEvaluateSuite:
    @pytest.fixture
    def service(self):
        from app.services.piston_service import PistonService
        return PistonService()

    @pytest.mark.asyncio
    async def test_evaluate_suite_unsupported_language_raises(self, service):
        from fastapi import HTTPException
        with pytest.raises(HTTPException, match="Unsupported"):
            await service.evaluate_suite("brainfuck", "code", [{"input": "1", "expected_output": "1", "hidden": False}])

    @pytest.mark.asyncio
    async def test_evaluate_suite_empty_cases_returns_empty(self, service):
        from unittest.mock import patch, AsyncMock
        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            results = await service.evaluate_suite("python", "code", [])
            assert results == []
            mock_exec.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_suite_mocked_python_runner(self, service):
        from unittest.mock import patch, AsyncMock
        from app.ports.code_executor import ExecutionResult
        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"6\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            results = await service.evaluate_suite(
                "python", "def add(a, b): return a + b",
                [{"input": "2\n4", "expected_output": "6", "hidden": False}],
            )
            assert len(results) == 1
            assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_evaluate_suite_build_runner_fallback(self, service):
        from unittest.mock import patch, AsyncMock
        from app.ports.code_executor import ExecutionResult
        with patch.object(service, 'execute', new=AsyncMock()) as mock_exec:
            mock_exec.return_value = ExecutionResult(
                stdout="@@SUITE_RESULT@@[{\"index\":1,\"passed\":true,\"actual\":\"42\"}]@@SUITE_RESULT@@",
                stderr="", exit_code=0,
            )
            raw_code = "def solve():\n    return 42"
            results = await service.evaluate_suite("cpp", raw_code, [{"input": "", "expected_output": "42", "hidden": False}])
            call_kwargs = mock_exec.call_args[1]
            assert call_kwargs["code"] == raw_code  # fallback: raw code unchanged
            assert len(results) == 1
