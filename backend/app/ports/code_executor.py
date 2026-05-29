from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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


@dataclass
class TestCaseResult:
    index: int = 0
    passed: bool = False
    input: str = ""
    expected: str = ""
    actual: str = ""
    hidden: bool = False


class CodeExecutor(ABC):
    @abstractmethod
    async def execute(
        self, language: str, code: str, stdin: str = "", version: Optional[str] = None
    ) -> ExecutionResult: ...

    @abstractmethod
    async def evaluate_suite(
        self,
        language: str,
        code: str,
        test_cases: List[dict],
    ) -> List[TestCaseResult]: ...

    @abstractmethod
    async def get_runtimes(self) -> List[dict]: ...

    def validate_code(self, language: str, code: str) -> dict:
        return {"valid": True, "warnings": [], "errors": []}
