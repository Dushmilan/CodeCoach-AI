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

    async def count_by_difficulty(self) -> Dict[str, int]:
        """Per-difficulty question counts (stats).

        Default materializes rows for adapter simplicity; SQL adapters
        override this with a GROUP BY aggregate.
        """
        questions = await self.get_all()
        counts = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            counts[q.difficulty.value] += 1
        return counts

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
        self,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[QuestionSummary]:
        questions = await self.get_all(difficulty=difficulty, category=category)
        summaries = [self._to_summary(q) for q in questions]
        if limit is None:
            return summaries[offset:]
        return summaries[offset : offset + limit]

    async def search_summaries(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[QuestionSummary]:
        questions = await self.search(query, difficulty=difficulty, category=category)
        summaries = [self._to_summary(q) for q in questions]
        if limit is None:
            return summaries[offset:]
        return summaries[offset : offset + limit]

    async def count_summaries(
        self,
        query: Optional[str] = None,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
    ) -> int:
        """Total rows matching the list filters (for page metadata)."""
        if query:
            return len(
                await self.search(query, difficulty=difficulty, category=category)
            )
        return len(await self.get_all(difficulty=difficulty, category=category))

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
