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


class TestFileExtension:
    def test_file_extensions(self):
        from app.services.piston_service import _get_file_extension
        assert _get_file_extension("python") == "py"
        assert _get_file_extension("javascript") == "js"
        assert _get_file_extension("java") == "java"
        assert _get_file_extension("cpp") == "cpp"
        assert _get_file_extension("unknown") == "txt"
