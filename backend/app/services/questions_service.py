import json
import os
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import logging
import asyncio

from app.models.schemas import Question, QuestionSummary, Difficulty
from app.models.question_validation_schemas import (
    QuestionValidationStatus,
    QuestionValidationResult,
)
from app.services.question_validator import QuestionValidatorService

logger = logging.getLogger(__name__)

class QuestionsService:
    """Service for managing coding questions and question bank."""

    def __init__(
        self, 
        questions_dir: str = "questions",
        validator: Optional[QuestionValidatorService] = None,
        validate_on_load: bool = False
    ):
        """
        Initialize the questions service.
        
        Args:
            questions_dir: Directory containing question JSON files
            validator: Question validator service (optional)
            validate_on_load: Whether to validate questions on load
        """
        self.questions_dir = questions_dir
        self.questions: Dict[str, Question] = {}
        self.validation_statuses: Dict[str, QuestionValidationStatus] = {}
        self.validator = validator
        self.validate_on_load = validate_on_load
        self._load_questions()

    def _load_questions(self):
        """Load questions from JSON files."""

        try:
            # Load sample questions
            sample_file = os.path.join(self.questions_dir, "sample_questions.json")
            if os.path.exists(sample_file):
                with open(sample_file, 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)
                    # Handle both list format and dict with 'questions' key
                    if isinstance(questions_data, dict):
                        questions_data = questions_data.get('questions', [])
                    for question_data in questions_data:
                        question = Question(**question_data)
                        self.questions[question.id] = question

                        # Initialize validation status
                        self.validation_statuses[question.id] = QuestionValidationStatus(
                            is_validated=False
                        )

                        # Validate if configured
                        if self.validate_on_load and self.validator:
                            self._validate_question_sync(question)
            else:
                logger.warning(f"Sample questions file not found: {sample_file}")

        except Exception as e:
            logger.error(f"Error loading questions: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error loading questions"
            )
    
    def _validate_question_sync(self, question: Question):
        """Synchronously validate a question (for use during loading)."""
        try:
            # asyncio.run() creates a new event loop and is the recommended approach
            result = asyncio.run(self.validator.validate_question(question))
            self._update_validation_status(question.id, result)
        except RuntimeError as e:
            # Handle case where we might be in an async context already
            logger.warning(f"Cannot run sync validation in async context for {question.id}: {e}")
        except Exception as e:
            logger.error(f"Error validating question {question.id}: {e}")
    
    def _update_validation_status(
        self, 
        question_id: str, 
        result: QuestionValidationResult
    ):
        """Update validation status for a question."""
        self.validation_statuses[question_id] = QuestionValidationStatus(
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
            ]
        )
    
    async def validate_question(
        self, 
        question_id: str,
        use_cases: Optional[List[str]] = None
    ) -> QuestionValidationResult:
        """
        Validate a specific question.
        
        Args:
            question_id: ID of the question to validate
            use_cases: Optional list of specific use cases to run
            
        Returns:
            QuestionValidationResult
            
        Raises:
            HTTPException: If question not found or validator not configured
        """
        if not self.validator:
            raise HTTPException(
                status_code=500,
                detail="Question validator not configured"
            )
        
        question = self.get_question_by_id(question_id)
        
        from app.models.question_validation_schemas import ValidationUseCase
        use_case_enums = None
        if use_cases:
            use_case_enums = [ValidationUseCase(uc) for uc in use_cases]
        
        result = await self.validator.validate_question(question, use_case_enums)
        self._update_validation_status(question_id, result)
        
        return result
    
    async def add_question(
        self, 
        question: Question,
        validate: bool = True
    ) -> QuestionValidationStatus:
        """
        Add a new question to the question bank.
        
        Args:
            question: The question to add
            validate: Whether to validate before adding
            
        Returns:
            QuestionValidationStatus
            
        Raises:
            HTTPException: If validation fails and validate=True
        """
        if validate and self.validator:
            result = await self.validator.validate_question(question)
            self._update_validation_status(question.id, result)
            
            if not result.valid:
                logger.warning(f"Question {question.id} failed validation")
                # Still add the question but mark as invalid
                self.questions[question.id] = question
                return self.validation_statuses[question.id]
        else:
            self.validation_statuses[question.id] = QuestionValidationStatus(
                is_validated=False
            )
        
        self.questions[question.id] = question
        return self.validation_statuses[question.id]
    
    def get_validation_status(self, question_id: str) -> QuestionValidationStatus:
        """
        Get validation status for a question.
        
        Args:
            question_id: ID of the question
            
        Returns:
            QuestionValidationStatus
            
        Raises:
            HTTPException: If question not found
        """
        if question_id not in self.questions:
            raise HTTPException(
                status_code=404,
                detail=f"Question not found: {question_id}"
            )
        
        return self.validation_statuses.get(
            question_id,
            QuestionValidationStatus(is_validated=False)
        )
    
    def get_invalid_questions(self) -> List[str]:
        """Get list of question IDs that failed validation."""
        return [
            qid for qid, status in self.validation_statuses.items()
            if status.is_validated and not status.validation_passed
        ]
    
    def get_unvalidated_questions(self) -> List[str]:
        """Get list of question IDs that haven't been validated."""
        return [
            qid for qid, status in self.validation_statuses.items()
            if not status.is_validated
        ]
    
    def get_all_questions(
        self,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> List[QuestionSummary]:
        """
        Get all questions with optional filtering.
        
        Args:
            difficulty: Filter by difficulty level
            category: Filter by category
            page: Page number for pagination
            per_page: Items per page
        
        Returns:
            List of question summaries
        """
        
        filtered_questions = list(self.questions.values())
        
        # Apply filters
        if difficulty:
            filtered_questions = [
                q for q in filtered_questions 
                if q.difficulty == difficulty
            ]
        
        if category:
            filtered_questions = [
                q for q in filtered_questions 
                if q.category.lower() == category.lower()
            ]
        
        # Convert to summaries
        summaries = [
            QuestionSummary(
                id=q.id,
                title=q.title,
                difficulty=q.difficulty,
                category=q.category,
                company_tags=q.company_tags,
                solved=False  # TODO: Implement user progress tracking
            )
            for q in filtered_questions
        ]
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return summaries[start_idx:end_idx]
    
    def get_question_by_id(self, question_id: str) -> Question:
        """
        Get a specific question by ID.
        
        Args:
            question_id: Unique question identifier
        
        Returns:
            Full question details
        """
        
        if question_id not in self.questions:
            raise HTTPException(
                status_code=404,
                detail=f"Question not found: {question_id}"
            )
        
        return self.questions[question_id]
    
    def get_questions_by_category(self, category: str) -> List[QuestionSummary]:
        """Get questions filtered by category."""
        
        questions = [
            q for q in self.questions.values() 
            if q.category.lower() == category.lower()
        ]
        
        return [
            QuestionSummary(
                id=q.id,
                title=q.title,
                difficulty=q.difficulty,
                category=q.category,
                company_tags=q.company_tags,
                solved=False
            )
            for q in questions
        ]
    
    def get_questions_by_difficulty(
        self, difficulty: Difficulty
    ) -> List[QuestionSummary]:
        """Get questions filtered by difficulty."""
        
        questions = [
            q for q in self.questions.values() 
            if q.difficulty == difficulty
        ]
        
        return [
            QuestionSummary(
                id=q.id,
                title=q.title,
                difficulty=q.difficulty,
                category=q.category,
                company_tags=q.company_tags,
                solved=False
            )
            for q in questions
        ]
    
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        
        categories = set()
        for question in self.questions.values():
            categories.add(question.category)
        
        return sorted(list(categories))
    
    def get_company_tags(self) -> List[str]:
        """Get all unique company tags."""
        
        companies = set()
        for question in self.questions.values():
            for company in question.company_tags:
                companies.add(company)
        
        return sorted(list(companies))
    
    def search_questions(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None
    ) -> List[QuestionSummary]:
        """
        Search questions by title or description.
        
        Args:
            query: Search query string
            difficulty: Optional difficulty filter
            category: Optional category filter
        
        Returns:
            List of matching questions
        """
        
        query = query.lower()
        
        filtered_questions = list(self.questions.values())
        
        # Apply text search
        matching_questions = [
            q for q in filtered_questions
            if query in q.title.lower() or query in q.description.lower()
        ]
        
        # Apply additional filters
        if difficulty:
            matching_questions = [
                q for q in matching_questions 
                if q.difficulty == difficulty
            ]
        
        if category:
            matching_questions = [
                q for q in matching_questions 
                if q.category.lower() == category.lower()
            ]
        
        return [
            QuestionSummary(
                id=q.id,
                title=q.title,
                difficulty=q.difficulty,
                category=q.category,
                company_tags=q.company_tags,
                solved=False
            )
            for q in matching_questions
        ]
    
    def get_total_count(self) -> int:
        """Get total number of questions."""
        return len(self.questions)
    
    def get_difficulty_counts(self) -> Dict[str, int]:
        """Get count of questions by difficulty."""
        
        counts = {"easy": 0, "medium": 0, "hard": 0}
        for question in self.questions.values():
            counts[question.difficulty.value] += 1
        
        return counts
    
    def get_category_counts(self) -> Dict[str, int]:
        """Get count of questions by category."""
        
        counts = {}
        for question in self.questions.values():
            category = question.category
            counts[category] = counts.get(category, 0) + 1
        
        return counts