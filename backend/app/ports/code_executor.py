from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ExecutionResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    signal: Optional[str] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[int] = None
    language: str = ""
    version: str = ""


class CodeExecutor(ABC):
    @abstractmethod
    async def execute(
        self, language: str, code: str, stdin: str = "", version: Optional[str] = None
    ) -> ExecutionResult: ...

    @abstractmethod
    async def get_runtimes(self) -> List[dict]: ...

    def validate_code(self, language: str, code: str) -> dict:
        return {"valid": True, "warnings": [], "errors": []}
