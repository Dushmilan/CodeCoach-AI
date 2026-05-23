from typing import Optional

from app.ports.code_executor import CodeExecutor, ExecutionResult
from app.services.piston_service import PistonService


class PistonExecutor(CodeExecutor):
    def __init__(self, piston_service: Optional[PistonService] = None):
        self._piston = piston_service or PistonService()

    async def execute(
        self, language: str, code: str, stdin: str = "", version: Optional[str] = None
    ) -> ExecutionResult:
        raw = await self._piston.execute_code(
            language, code, stdin=stdin, version=version
        )
        return ExecutionResult(
            stdout=raw.get("stdout", ""),
            stderr=raw.get("stderr", ""),
            exit_code=raw.get("exit_code", 0),
            language=raw.get("language", language),
            version=raw.get("version", version or ""),
        )

    async def get_runtimes(self) -> list[dict]:
        return await self._piston.get_runtimes()

    def validate_code(self, language: str, code: str) -> dict:
        return self._piston.validate_code(language, code)
