from abc import ABC, abstractmethod


class CodeWrapper(ABC):
    @abstractmethod
    def wrap(self, code: str) -> str: ...
