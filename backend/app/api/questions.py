from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
import logging

from app.models.schemas import Question, QuestionsListResponse, Difficulty
from app.services.question_bank import QuestionBank, QuestionFilters
from app.api.dependencies import get_question_bank
from app.middleware.rate_limit import limiter, QUESTIONS_RATE_LIMIT

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=QuestionsListResponse)
@router.get("/", response_model=QuestionsListResponse)
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_questions(
    request: Request,
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=200, description="Items per page"),
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
    except Exception:
        logger.exception("Failed to fetch questions")
        raise HTTPException(status_code=500, detail="Failed to fetch questions")


@router.get("/categories")
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_categories(
    request: Request,
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        stats = await bank.stats()
        return {"categories": stats.categories}
    except Exception:
        logger.exception("Failed to fetch categories")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


@router.get("/companies")
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_companies(
    request: Request,
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        stats = await bank.stats()
        return {"companies": stats.companies}
    except Exception:
        logger.exception("Failed to fetch companies")
        raise HTTPException(status_code=500, detail="Failed to fetch companies")


@router.get("/search")
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def search_questions(
    request: Request,
    q: str = Query(..., description="Search query"),
    difficulty: Optional[Difficulty] = Query(None, description="Filter by difficulty"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=200, description="Items per page"),
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")

        result = await bank.query(
            QuestionFilters(
                query=q,
                difficulty=difficulty,
                category=category,
                page=page,
                per_page=per_page,
            )
        )

        return QuestionsListResponse(
            questions=result.items,
            total=result.total,
            page=page,
            per_page=per_page,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to search questions")
        raise HTTPException(status_code=500, detail="Failed to search questions")


@router.get("/stats")
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_question_stats(
    request: Request,
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
    except Exception:
        logger.exception("Failed to fetch statistics")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/{question_id}", response_model=Question)
@limiter.limit(QUESTIONS_RATE_LIMIT)
async def get_question(
    request: Request,
    question_id: str,
    bank: QuestionBank = Depends(get_question_bank),
):
    try:
        return await bank.get(question_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch question %s", question_id)
        raise HTTPException(status_code=500, detail="Failed to fetch question")
