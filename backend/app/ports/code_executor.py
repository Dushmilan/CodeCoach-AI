from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    language: str = ""
    version: str = ""


class CodeExecutor(ABC):
    @abstractmethod
    async def execute(
        self, language: str, code: str, stdin: str = "", version: Optional[str] = None
    ) -> ExecutionResult: ...

    @abstractmethod
    async def get_runtimes(self) -> list[dict]: ...

    def validate_code(self, language: str, code: str) -> dict:
        return {"valid": True, "warnings": [], "errors": []}
