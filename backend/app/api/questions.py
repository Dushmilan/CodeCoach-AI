from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.schemas import (
    Question, QuestionSummary, QuestionsListResponse, 
    Difficulty
)
from app.services.questions_service import QuestionsService

router = APIRouter()

# Initialize questions service
questions_service = QuestionsService()

@router.get("/", response_model=QuestionsListResponse)
async def get_questions(
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get all questions with optional filtering and pagination.
    
    Supports filtering by difficulty and category, with pagination.
    """
    
    try:
        questions = questions_service.get_all_questions(
            difficulty=difficulty,
            category=category,
            page=page,
            per_page=per_page
        )
        
        total = questions_service.get_total_count()
        
        # Apply filtering to total count
        if difficulty or category:
            filtered_total = len(questions_service.get_all_questions(
                difficulty=difficulty,
                category=category,
                page=1,
                per_page=10000  # Get all for count
            ))
        else:
            filtered_total = total
        
        return QuestionsListResponse(
            questions=questions,
            total=filtered_total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching questions: {str(e)}"
        )

@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str):
    """
    Get a specific question by ID.
    
    Returns full question details including description, examples, test cases, and starter code.
    """
    
    try:
        question = questions_service.get_question_by_id(question_id)
        return question
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching question: {str(e)}"
        )

@router.get("/categories")
async def get_categories():
    """Get all available question categories."""
    
    try:
        categories = questions_service.get_categories()
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching categories: {str(e)}"
        )

@router.get("/companies")
async def get_companies():
    """Get all company tags used in questions."""
    
    try:
        companies = questions_service.get_company_tags()
        return {"companies": companies}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching companies: {str(e)}"
        )

@router.get("/search")
async def search_questions(
    q: str = Query(..., description="Search query"),
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Search questions by title or description.
    
    Supports text search with optional difficulty and category filters.
    """
    
    try:
        if not q.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        all_results = questions_service.search_questions(
            query=q,
            difficulty=difficulty,
            category=category
        )
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = all_results[start_idx:end_idx]
        
        return QuestionsListResponse(
            questions=paginated_results,
            total=len(all_results),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching questions: {str(e)}"
        )

@router.get("/stats")
async def get_question_stats():
    """Get statistics about the question bank."""
    
    try:
        total = questions_service.get_total_count()
        difficulty_counts = questions_service.get_difficulty_counts()
        category_counts = questions_service.get_category_counts()
        
        return {
            "total": total,
            "difficulty_counts": difficulty_counts,
            "category_counts": category_counts,
            "categories": questions_service.get_categories(),
            "companies": questions_service.get_company_tags()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching statistics: {str(e)}"
        )

@router.get("/category/{category}")
async def get_questions_by_category(
    category: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get questions filtered by category."""
    
    try:
        questions = questions_service.get_questions_by_category(category)
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_questions = questions[start_idx:end_idx]
        
        return QuestionsListResponse(
            questions=paginated_questions,
            total=len(questions),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching questions by category: {str(e)}"
        )

@router.get("/difficulty/{difficulty}")
async def get_questions_by_difficulty(
    difficulty: Difficulty,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get questions filtered by difficulty."""
    
    try:
        questions = questions_service.get_questions_by_difficulty(difficulty)
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_questions = questions[start_idx:end_idx]
        
        return QuestionsListResponse(
            questions=paginated_questions,
            total=len(questions),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching questions by difficulty: {str(e)}"
        )