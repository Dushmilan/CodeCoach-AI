from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.models.schemas import Question, QuestionsListResponse, Difficulty
from app.services.question_bank import QuestionBank, QuestionFilters
from app.api.dependencies import get_question_bank

router = APIRouter()


@router.get("/", response_model=QuestionsListResponse)
async def get_questions(
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=100, description="Items per page"),
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        result = await bank.query(
            QuestionFilters(
                difficulty=difficulty, category=category, page=page, per_page=per_page
            )
        )
        return QuestionsListResponse(
            questions=result.items, total=result.total, page=page, per_page=per_page
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching questions: {str(e)}"
        )


@router.get("/categories")
async def get_categories(
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        stats = await bank.stats()
        return {"categories": stats.categories}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching categories: {str(e)}"
        )


@router.get("/companies")
async def get_companies(
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        stats = await bank.stats()
        return {"companies": stats.companies}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching companies: {str(e)}"
        )


@router.get("/search")
async def search_questions(
    q: str = Query(..., description="Search query"),
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=100, description="Items per page"),
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")

        result = await bank.query(
            QuestionFilters(
                query=q, difficulty=difficulty, category=category, per_page=10000
            )
        )

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = result.items[start_idx:end_idx]

        return QuestionsListResponse(
            questions=paginated,
            total=result.total,
            page=page,
            per_page=per_page,
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching questions: {str(e)}"
        )


@router.get("/stats")
async def get_question_stats(
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        stats = await bank.stats()
        return {
            "total": stats.total,
            "difficulty_counts": stats.difficulty_counts,
            "category_counts": stats.category_counts,
            "categories": stats.categories,
            "companies": stats.companies,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching statistics: {str(e)}"
        )


@router.get("/{question_id}", response_model=Question)
async def get_question(
    question_id: str,
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        return await bank.get(question_id)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching question: {str(e)}"
        )
