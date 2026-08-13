from fastapi import APIRouter, Depends, HTTPException
from typing import AsyncGenerator, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.dependencies import get_question_bank
from app.core.database import get_db
from app.models.auth_schemas import UserResponse
from app.models.schemas import Question
from app.models.skill_graph_schemas import (
    EventIngestResult,
    LearningEvent,
    Recommendation,
    RecommendedQuestion,
    SkillGraphResponse,
)
from app.ports.skill_graph_repository import SkillGraphRepository
from app.repositories.sql_skill_graph_repository import SqlSkillGraphRepository
from app.services.question_bank import QuestionBank
from app.services.skill_graph_service import SkillGraphService

router = APIRouter()


async def get_skill_graph_repo(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SkillGraphRepository, None]:
    yield SqlSkillGraphRepository(db)


def get_skill_graph_service(
    repo: SkillGraphRepository = Depends(get_skill_graph_repo),
) -> SkillGraphService:
    return SkillGraphService(repository=repo)


@router.get("/me/skills", response_model=SkillGraphResponse)
async def get_my_skills(
    current_user: UserResponse = Depends(get_current_user),
    service: SkillGraphService = Depends(get_skill_graph_service),
):
    try:
        return await service.get_graph(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching skills: {e}")


@router.get("/me/recommendations", response_model=List[Recommendation])
async def get_my_recommendations(
    limit: int = 5,
    current_user: UserResponse = Depends(get_current_user),
    service: SkillGraphService = Depends(get_skill_graph_service),
):
    try:
        return await service.get_recommendations(current_user.id, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching recommendations: {e}"
        )


@router.get("/me/recommended-questions", response_model=List[RecommendedQuestion])
async def get_my_recommended_questions(
    limit: int = 5,
    current_user: UserResponse = Depends(get_current_user),
    service: SkillGraphService = Depends(get_skill_graph_service),
    question_bank: QuestionBank = Depends(get_question_bank),
):
    """Recommendations resolved to concrete practice questions.

    A recommended question that no longer exists in the bank is skipped rather
    than failing the whole response.
    """

    async def load_question(question_id: str) -> Optional[Question]:
        try:
            return await question_bank.get(question_id)
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise

    try:
        return await service.get_recommended_questions(
            current_user.id, load_question, limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching recommended questions: {e}",
        )


@router.post("/events", response_model=EventIngestResult)
async def ingest_events(
    events: List[LearningEvent],
    current_user: UserResponse = Depends(get_current_user),
    service: SkillGraphService = Depends(get_skill_graph_service),
):
    """Persist learning events and update the caller's skill graph.

    Events must carry an ``id`` for idempotency. The client-supplied
    ``user_id`` is never trusted: every event is attributed to the
    authenticated caller so users cannot write to someone else's history.
    """
    for event in events:
        event.user_id = current_user.id
    try:
        return await service.ingest_events(events, user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting events: {e}")


@router.delete("/me/history")
async def delete_my_history(
    current_user: UserResponse = Depends(get_current_user),
    service: SkillGraphService = Depends(get_skill_graph_service),
):
    """Delete the caller's learning history (events + skill states)."""
    await service.delete_history(current_user.id)
    return {"status": "ok"}
