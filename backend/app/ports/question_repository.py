from abc import ABC, abstractmethod
from typing import Optional

from app.models.schemas import Question, Difficulty


class QuestionRepository(ABC):
    @abstractmethod
    async def get_all(self, difficulty: Optional[Difficulty] = None, category: Optional[str] = None) -> list[Question]:
        ...

    @abstractmethod
    async def get_by_id(self, question_id: str) -> Optional[Question]:
        ...

    @abstractmethod
    async def search(self, query: str, difficulty: Optional[Difficulty] = None, category: Optional[str] = None) -> list[Question]:
        ...

    @abstractmethod
    async def get_categories(self) -> list[str]:
        ...

    @abstractmethod
    async def get_company_tags(self) -> list[str]:
        ...

    @abstractmethod
    async def add(self, question: Question) -> None:
        ...
