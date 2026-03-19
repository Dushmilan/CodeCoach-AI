import json
import os
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
import logging

from app.models.schemas import Question, QuestionSummary, Difficulty

logger = logging.getLogger(__name__)

class QuestionsService:
    """Service for managing coding questions and question bank."""
    
    def __init__(self, questions_dir: str = "questions"):
        self.questions_dir = questions_dir
        self.questions = {}
        self._load_questions()
    
    def _load_questions(self):
        """Load questions from JSON files."""
        
        try:
            # Load sample questions
            sample_file = os.path.join(self.questions_dir, "sample_questions.json")
            if os.path.exists(sample_file):
                with open(sample_file, 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)
                    for question_data in questions_data:
                        question = Question(**question_data)
                        self.questions[question.id] = question
            else:
                logger.warning(f"Sample questions file not found: {sample_file}")
                
        except Exception as e:
            logger.error(f"Error loading questions: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error loading questions"
            )
    
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