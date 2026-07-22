from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.models.schemas import Question, QuestionSummary, Difficulty


class QuestionRepository(ABC):
    @abstractmethod
    async def get_all(
        self, difficulty: Optional[Difficulty] = None, category: Optional[str] = None
    ) -> List[Question]: ...

    async def count(
        self, difficulty: Optional[Difficulty] = None, category: Optional[str] = None
    ) -> int:
        return len(await self.get_all(difficulty=difficulty, category=category))

    @abstractmethod
    async def get_by_id(self, question_id: str) -> Optional[Question]: ...

    @abstractmethod
    async def search(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
    ) -> List[Question]: ...

    @abstractmethod
    async def get_categories(self) -> List[str]: ...

    @abstractmethod
    async def get_company_tags(self) -> List[str]: ...

    @abstractmethod
    async def add(self, question: Question) -> None: ...

    async def get_summaries(
        self, difficulty: Optional[Difficulty] = None, category: Optional[str] = None
    ) -> List[QuestionSummary]:
        questions = await self.get_all(difficulty=difficulty, category=category)
        return [self._to_summary(q) for q in questions]

    async def search_summaries(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
    ) -> List[QuestionSummary]:
        questions = await self.search(query, difficulty=difficulty, category=category)
        return [self._to_summary(q) for q in questions]

    async def save_validation_status(self, question_id: str, status: Any) -> None:
        pass

    async def get_validation_statuses(self) -> Dict[str, Any]:
        return {}

    def _to_summary(self, question: Question) -> QuestionSummary:
        return QuestionSummary(
            id=question.id,
            title=question.title,
            difficulty=question.difficulty,
            category=question.category,
            company_tags=question.company_tags,
            solved=False,
        )
