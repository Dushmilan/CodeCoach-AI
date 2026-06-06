from abc import ABC, abstractmethod
from typing import Any, Dict, List


class CodeWrapper(ABC):
    @abstractmethod
    def wrap(self, code: str) -> str: ...

    @abstractmethod
    def wrap_with_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> str: ...
