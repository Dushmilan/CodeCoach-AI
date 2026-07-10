"""QuestionsService — thin wrapper delegating to QuestionBank.

Kept for backward compatibility. New callers should use QuestionBank directly.
"""

from typing import List, Dict, Optional
from fastapi import HTTPException
import logging

from app.models.schemas import Question, QuestionSummary, Difficulty
from app.models.question_validation_schemas import (
    QuestionValidationStatus,
    QuestionValidationResult,
)
from app.ports.question_repository import QuestionRepository
from app.repositories.file_question_repository import FileQuestionRepository
from app.services.question_validator import QuestionValidatorService
from app.services.question_bank import QuestionBank, QuestionFilters
from app.services.redis_service import RedisCache

logger = logging.getLogger(__name__)


class QuestionsService:
    """Thin wrapper around QuestionBank for backward compatibility."""

    def __init__(
        self,
        repository: Optional[QuestionRepository] = None,
        validator: Optional[QuestionValidatorService] = None,
        cache: Optional[RedisCache] = None,
    ):
        repo = repository or FileQuestionRepository("questions/sample_questions.json")
        self._bank = QuestionBank(repository=repo, validator=validator, cache=cache)
        self.repository = repo
        self.validator = validator
        self.cache = cache

    async def validate_question(
        self, question_id: str, use_cases: Optional[List[str]] = None
    ) -> QuestionValidationResult:
        if not self._bank._validator:
            raise HTTPException(
                status_code=500, detail="Question validator not configured"
            )

        question = await self._bank.get(question_id)

        from app.models.question_validation_schemas import ValidationUseCase

        use_case_enums = None
        if use_cases:
            use_case_enums = [ValidationUseCase(uc) for uc in use_cases]

        result = await self._bank._validator.validate_question(question, use_case_enums)
        await self._bank._persist_validation_status(question_id, result)
        return result

    async def add_question(
        self, question: Question, validate: bool = True
    ) -> QuestionValidationStatus:
        return await self._bank.add(question, validate=validate)

    async def get_all_questions(
        self,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> List[QuestionSummary]:
        result = await self._bank.query(
            QuestionFilters(
                difficulty=difficulty, category=category, page=page, per_page=per_page
            )
        )
        return result.items

    async def get_question_by_id(self, question_id: str) -> Question:
        return await self._bank.get(question_id)

    async def get_questions_by_category(self, category: str) -> List[QuestionSummary]:
        result = await self._bank.query(
            QuestionFilters(category=category, per_page=10000)
        )
        return result.items

    async def get_questions_by_difficulty(
        self, difficulty: Difficulty
    ) -> List[QuestionSummary]:
        result = await self._bank.query(
            QuestionFilters(difficulty=difficulty, per_page=10000)
        )
        return result.items

    async def get_categories(self) -> List[str]:
        stats = await self._bank.stats()
        return stats.categories

    async def get_company_tags(self) -> List[str]:
        stats = await self._bank.stats()
        return stats.companies

    async def search_questions(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
    ) -> List[QuestionSummary]:
        result = await self._bank.query(
            QuestionFilters(
                query=query, difficulty=difficulty, category=category, per_page=10000
            )
        )
        return result.items

    async def get_total_count(self) -> int:
        stats = await self._bank.stats()
        return stats.total

    async def get_difficulty_counts(self) -> Dict[str, int]:
        stats = await self._bank.stats()
        return stats.difficulty_counts

    async def get_category_counts(self) -> Dict[str, int]:
        stats = await self._bank.stats()
        return stats.category_counts
