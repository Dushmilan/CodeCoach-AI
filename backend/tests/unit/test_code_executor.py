import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.ports.code_executor import CodeExecutor, ExecutionResult
from app.services.piston_service import PistonService


class TestPistonServiceImplementsCodeExecutor:
    def test_conforms_to_port(self):
        assert isinstance(PistonService(), CodeExecutor)

    @pytest.mark.asyncio
    async def test_execute_returns_execution_result(self):
        service = PistonService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "run": {
                    "stdout": "hello\n",
                    "stderr": "",
                    "code": 0,
                    "wall_time": 0.01,
                },
                "language": "python",
                "version": "3.10.0",
            }
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await service.execute("python", "print(1)")

        assert isinstance(result, ExecutionResult)
        assert result.stdout == "hello\n"
        assert result.exit_code == 0
        assert result.execution_time == 0.01

    @pytest.mark.asyncio
    async def test_execute_unknown_language_raises(self):
        service = PistonService()

        with pytest.raises(Exception):
            await service.execute("brainfuck", "+++")

    @pytest.mark.asyncio
    async def test_get_runtimes_returns_list(self):
        service = PistonService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value=[{"language": "python", "version": "3.11.0"}]
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            runtimes = await service.get_runtimes()

        assert isinstance(runtimes, list)
        assert runtimes[0]["language"] == "python"

    def test_validate_code_returns_dict(self):
        service = PistonService()
        result = service.validate_code("python", "print(1)")
        assert result["valid"] is True
