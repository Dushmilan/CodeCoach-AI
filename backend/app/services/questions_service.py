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

logger = logging.getLogger(__name__)


class QuestionsService:
    """Service for managing coding questions and question bank."""

    def __init__(
        self,
        repository: Optional[QuestionRepository] = None,
        validator: Optional[QuestionValidatorService] = None,
    ):
        self.repository = repository or FileQuestionRepository(
            "questions/sample_questions.json"
        )
        self.validator = validator

    async def validate_question(
        self, question_id: str, use_cases: Optional[List[str]] = None
    ) -> QuestionValidationResult:
        if not self.validator:
            raise HTTPException(
                status_code=500, detail="Question validator not configured"
            )

        question = await self.repository.get_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=404, detail=f"Question not found: {question_id}"
            )

        from app.models.question_validation_schemas import ValidationUseCase

        use_case_enums = None
        if use_cases:
            use_case_enums = [ValidationUseCase(uc) for uc in use_cases]

        result = await self.validator.validate_question(question, use_case_enums)
        await self._persist_validation_status(question_id, result)
        return result

    async def add_question(
        self, question: Question, validate: bool = True
    ) -> QuestionValidationStatus:
        if validate and self.validator:
            result = await self.validator.validate_question(question)
            await self._persist_validation_status(question.id, result)

            if not result.valid:
                logger.warning(f"Question {question.id} failed validation")
                await self.repository.add(question)
                return QuestionValidationStatus(
                    is_validated=True, validation_passed=False
                )
        else:
            await self.repository.add(question)
            return QuestionValidationStatus(is_validated=False)

        await self.repository.add(question)
        return QuestionValidationStatus(is_validated=True, validation_passed=True)

    async def get_all_questions(
        self,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> List[QuestionSummary]:
        summaries = await self.repository.get_summaries(
            difficulty=difficulty, category=category
        )
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        return summaries[start_idx:end_idx]

    async def get_question_by_id(self, question_id: str) -> Question:
        question = await self.repository.get_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=404, detail=f"Question not found: {question_id}"
            )
        return question

    async def get_questions_by_category(self, category: str) -> List[QuestionSummary]:
        return await self.repository.get_summaries(category=category)

    async def get_questions_by_difficulty(
        self, difficulty: Difficulty
    ) -> List[QuestionSummary]:
        return await self.repository.get_summaries(difficulty=difficulty)

    async def get_categories(self) -> List[str]:
        return await self.repository.get_categories()

    async def get_company_tags(self) -> List[str]:
        return await self.repository.get_company_tags()

    async def search_questions(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
    ) -> List[QuestionSummary]:
        return await self.repository.search_summaries(
            query, difficulty=difficulty, category=category
        )

    async def get_total_count(self) -> int:
        questions = await self.repository.get_all()
        return len(questions)

    async def get_difficulty_counts(self) -> Dict[str, int]:
        questions = await self.repository.get_all()
        counts = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            counts[q.difficulty.value] += 1
        return counts

    async def get_category_counts(self) -> Dict[str, int]:
        questions = await self.repository.get_all()
        counts = {}
        for q in questions:
            counts[q.category] = counts.get(q.category, 0) + 1
        return counts

    async def _persist_validation_status(
        self, question_id: str, result: QuestionValidationResult
    ):
        status = QuestionValidationStatus(
            is_validated=True,
            last_validated=result.validated_at,
            validation_passed=result.valid,
            validation_errors=[
                issue.message
                for r in result.results.values()
                for issue in r.issues
                if issue.severity.value == "error"
            ],
            validation_warnings=[
                issue.message
                for r in result.results.values()
                for issue in r.issues
                if issue.severity.value == "warning"
            ],
        )
        await self.repository.save_validation_status(question_id, status)
