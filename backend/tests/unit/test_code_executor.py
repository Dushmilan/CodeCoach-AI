import pytest
from unittest.mock import AsyncMock

from app.ports.code_executor import CodeExecutor, ExecutionResult


class MockPistonService:
    def __init__(self):
        self.execute_code = AsyncMock(return_value={
            "stdout": "hello\n", "stderr": "", "exit_code": 0,
            "language": "python", "version": "3.11.0"
        })
        self.get_runtimes = AsyncMock(return_value=[
            {"language": "python", "version": "3.11.0"}
        ])

    def validate_code(self, language, code):
        return {"valid": True, "warnings": [], "errors": []}


class TestPistonExecutor:
    @pytest.fixture
    def mock_piston(self):
        return MockPistonService()

    @pytest.mark.asyncio
    async def test_execute_returns_execution_result(self, mock_piston):
        from app.adapters.piston_executor import PistonExecutor

        executor = PistonExecutor(piston_service=mock_piston)
        result = await executor.execute("python", "print(1)")

        assert isinstance(result, ExecutionResult)
        assert result.stdout == "hello\n"
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_execute_passes_stdin(self, mock_piston):
        from app.adapters.piston_executor import PistonExecutor

        executor = PistonExecutor(piston_service=mock_piston)
        await executor.execute("python", "input()", stdin="world")

        mock_piston.execute_code.assert_called_with(
            "python", "input()", stdin="world", version=None
        )

    @pytest.mark.asyncio
    async def test_get_runtimes_delegates(self, mock_piston):
        from app.adapters.piston_executor import PistonExecutor

        executor = PistonExecutor(piston_service=mock_piston)
        runtimes = await executor.get_runtimes()

        assert runtimes == [{"language": "python", "version": "3.11.0"}]

    def test_validate_code_delegates(self, mock_piston):
        from app.adapters.piston_executor import PistonExecutor

        executor = PistonExecutor(piston_service=mock_piston)
        result = executor.validate_code("python", "code")

        assert result["valid"] is True

    def test_conforms_to_port(self):
        from app.adapters.piston_executor import PistonExecutor

        assert isinstance(PistonExecutor(piston_service=MockPistonService()), CodeExecutor)
