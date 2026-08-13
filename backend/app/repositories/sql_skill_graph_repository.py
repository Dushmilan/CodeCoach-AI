from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import (
    LearningEventORM,
    QuestionSkillORM,
    SkillORM,
    UserSkillStateORM,
)
from app.models.skill_graph_schemas import (
    LearningEvent,
    LearningEventType,
    QuestionSkill,
    Skill,
    SkillStatus,
    Trend,
    UserSkillState,
)
from app.ports.skill_graph_repository import SkillGraphRepository


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class SqlSkillGraphRepository(SkillGraphRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- skills taxonomy ------------------------------------------------
    async def list_skills(self) -> List[Skill]:
        result = await self.session.execute(select(SkillORM).order_by(SkillORM.slug))
        return [
            Skill(
                slug=row.slug,
                name=row.name,
                description=row.description or "",
                parent_id=row.parent_id,
                prerequisite_ids=row.prerequisite_ids or [],
            )
            for row in result.scalars().all()
        ]

    async def get_question_skills(self) -> List[QuestionSkill]:
        result = await self.session.execute(select(QuestionSkillORM))
        return [
            QuestionSkill(
                question_id=row.question_id,
                skill_slug=row.skill_slug,
                weight=_to_float(row.weight),
            )
            for row in result.scalars().all()
        ]

    # --- events ----------------------------------------------------------
    async def event_exists(self, event_id: str) -> bool:
        result = await self.session.execute(
            select(LearningEventORM.id).where(LearningEventORM.id == event_id)
        )
        return result.scalar_one_or_none() is not None

    async def save_event(self, event: LearningEvent) -> None:
        self.session.add(
            LearningEventORM(
                id=event.id,
                user_id=event.user_id,
                event_type=event.event_type.value,
                question_id=event.question_id,
                lesson_id=event.lesson_id,
                skill_slug=event.skill_slug,
                event_metadata=event.metadata or {},
                occurred_at=event.occurred_at,
            )
        )
        await self.session.commit()

    async def get_user_events(
        self, user_id: str, since: Optional[object] = None
    ) -> List[LearningEvent]:
        query = select(LearningEventORM).where(LearningEventORM.user_id == user_id)
        if since is not None:
            query = query.where(LearningEventORM.occurred_at >= since)
        result = await self.session.execute(
            query.order_by(LearningEventORM.occurred_at)
        )
        return [
            LearningEvent(
                id=row.id,
                user_id=row.user_id,
                event_type=LearningEventType(row.event_type),
                question_id=row.question_id,
                lesson_id=row.lesson_id,
                skill_slug=row.skill_slug,
                metadata=row.event_metadata or {},
                occurred_at=row.occurred_at,
            )
            for row in result.scalars().all()
        ]

    # --- states -----------------------------------------------------------
    async def get_states(self, user_id: str) -> Dict[str, UserSkillState]:
        result = await self.session.execute(
            select(UserSkillStateORM).where(UserSkillStateORM.user_id == user_id)
        )
        states: Dict[str, UserSkillState] = {}
        for row in result.scalars().all():
            states[row.skill_slug] = UserSkillState(
                user_id=row.user_id,
                skill_slug=row.skill_slug,
                mastery_score=_to_float(row.mastery_score),
                confidence=_to_float(row.confidence),
                evidence_count=row.evidence_count or 0,
                recent_error_count=row.recent_error_count or 0,
                distinct_question_ids=row.distinct_question_ids or [],
                last_seen_at=row.last_seen_at,
                last_reviewed_at=row.last_reviewed_at,
                status=SkillStatus.NEW,
                trend=Trend.STABLE,
            )
        return states

    async def save_state(self, state: UserSkillState) -> None:
        result = await self.session.execute(
            select(UserSkillStateORM).where(
                UserSkillStateORM.user_id == state.user_id,
                UserSkillStateORM.skill_slug == state.skill_slug,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = UserSkillStateORM(
                id=f"{state.user_id}:{state.skill_slug}",
                user_id=state.user_id,
                skill_slug=state.skill_slug,
            )
            self.session.add(row)
        row.mastery_score = state.mastery_score
        row.confidence = state.confidence
        row.evidence_count = state.evidence_count
        row.recent_error_count = state.recent_error_count
        row.distinct_question_ids = state.distinct_question_ids
        row.last_seen_at = state.last_seen_at
        row.last_reviewed_at = state.last_reviewed_at
        await self.session.commit()

    async def delete_user_history(self, user_id: str) -> None:
        await self.session.execute(
            delete(LearningEventORM).where(LearningEventORM.user_id == user_id)
        )
        await self.session.execute(
            delete(UserSkillStateORM).where(UserSkillStateORM.user_id == user_id)
        )
        await self.session.commit()
