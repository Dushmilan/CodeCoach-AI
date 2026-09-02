from __future__ import annotations

from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, List, Optional

from app.models.schemas import Question
from app.models.skill_graph_schemas import (
    EventIngestResult,
    LearningEvent,
    QuestionSkill,
    Recommendation,
    RecommendedQuestion,
    Skill,
    SkillGraphEdge,
    SkillGraphResponse,
    SkillSummary,
    UserSkillState,
)
from app.ports.skill_graph_repository import SkillGraphRepository
from app.models.skill_graph_schemas import SkillStatus, Trend

from app.services.skill_graph_rules import (
    apply_event,
    decay_state,
    mastery_for_status,
    recommend,
)


class SkillGraphService:
    """Orchestrates the deterministic Personal Skill Graph.

    Pure rule logic lives in ``skill_graph_rules``; this service wires events
    to skills (via question mappings or explicit slugs), persists them, and
    derives the graph + recommendations. No ML anywhere in this path.
    """

    def __init__(self, repository: SkillGraphRepository):
        self.repository = repository

    async def _load_taxonomy(
        self,
    ) -> tuple[Dict[str, Skill], Dict[str, List[QuestionSkill]]]:
        skills = await self.repository.list_skills()
        question_skills = await self.repository.get_question_skills()
        skills_by_slug = {s.slug: s for s in skills}
        question_skills_by_q: Dict[str, List[QuestionSkill]] = {}
        for qs in question_skills:
            question_skills_by_q.setdefault(qs.question_id, []).append(qs)
        return skills_by_slug, question_skills_by_q

    @staticmethod
    def _attributed_skills(
        event: LearningEvent,
        skills_by_slug: Dict[str, Skill],
        question_skills_by_q: Dict[str, List[QuestionSkill]],
    ) -> List[QuestionSkill]:
        """Resolve which skills an event touches.

        Explicit skill_slug wins; otherwise the question's skill mapping is
        used; an unmapped question attributes to nothing (cannot corrupt the
        graph).
        """
        if event.skill_slug:
            if event.skill_slug in skills_by_slug:
                return [
                    QuestionSkill(
                        question_id=event.question_id or "",
                        skill_slug=event.skill_slug,
                        weight=1.0,
                    )
                ]
            return []
        if event.question_id:
            return question_skills_by_q.get(event.question_id, [])
        return []

    async def ingest_events(
        self, events: List[LearningEvent], user_id: Optional[str] = None
    ) -> EventIngestResult:
        skills_by_slug, question_skills_by_q = await self._load_taxonomy()
        result = EventIngestResult()

        for event in events:
            if user_id and event.user_id != user_id:
                result.invalid += 1
                continue
            if not event.id:
                result.skipped += 1
                continue
            if await self.repository.event_exists(event.id):
                result.duplicate += 1
                continue

            attributed = self._attributed_skills(
                event, skills_by_slug, question_skills_by_q
            )

            await self.repository.save_event(event)
            result.accepted += 1

            if attributed:
                states = await self.repository.get_states(event.user_id)
                for mapping in attributed:
                    state = states.get(mapping.skill_slug)
                    if state is None:
                        state = UserSkillState(
                            user_id=event.user_id, skill_slug=mapping.skill_slug
                        )
                    new_state = apply_event(state, event)
                    await self.repository.save_state(new_state)

        return result

    async def get_graph(
        self,
        user_id: str,
        now: Optional[datetime] = None,
        include_boilerplate: bool = False,
    ) -> SkillGraphResponse:
        now = now or datetime.now(timezone.utc)
        skills_by_slug, _ = await self._load_taxonomy()
        states = await self.repository.get_states(user_id)

        summaries: List[SkillSummary] = []
        for slug, skill in skills_by_slug.items():
            state = states.get(slug)
            if state is None:
                if not include_boilerplate:
                    continue
                summaries.append(
                    SkillSummary(
                        skill_slug=slug,
                        name=skill.name,
                        mastery_score=0.0,
                        confidence=0.0,
                        status=SkillStatus.NEW,
                        trend=Trend.STABLE,
                        evidence_count=0,
                        recent_error_count=0,
                        last_seen_at=None,
                        last_reviewed_at=None,
                    )
                )
                continue
            decayed = decay_state(state, now)
            summaries.append(
                SkillSummary(
                    skill_slug=slug,
                    name=skill.name,
                    mastery_score=round(decayed.mastery_score, 3),
                    confidence=round(decayed.confidence, 3),
                    # Status is always derived from mastery (never from a
                    # stored value that could be stale), so thresholds stay
                    # authoritative.
                    status=mastery_for_status(decayed.mastery_score),
                    trend=decayed.trend,
                    evidence_count=decayed.evidence_count,
                    recent_error_count=decayed.recent_error_count,
                    last_seen_at=decayed.last_seen_at,
                    last_reviewed_at=decayed.last_reviewed_at,
                )
            )
        # Boilerplate-first: stable learners see full taxonomy sorted by mastery;
        # new users (all 0.0) keep taxonomy insertion order.
        if include_boilerplate:
            summaries.sort(key=lambda s: (-s.mastery_score, s.skill_slug))
        else:
            summaries.sort(key=lambda s: s.mastery_score, reverse=True)

        edges = [
            SkillGraphEdge(source=prereq, target=slug, relation="prerequisite")
            for slug, skill in skills_by_slug.items()
            for prereq in skill.prerequisite_ids
            if prereq in skills_by_slug
        ]
        return SkillGraphResponse(skills=summaries, edges=edges)

    async def get_boilerplate_graph(self) -> SkillGraphResponse:
        """Deterministic boilerplate graph — no user state, all skills NEW.

        Used for onboarding previews and unauthenticated tour. Pure taxonomy,
        no DB state reads beyond the skill list.
        """
        skills_by_slug, _ = await self._load_taxonomy()
        summaries = [
            SkillSummary(
                skill_slug=slug,
                name=skill.name,
                mastery_score=0.0,
                confidence=0.0,
                status=SkillStatus.NEW,
                trend=Trend.STABLE,
                evidence_count=0,
                recent_error_count=0,
                last_seen_at=None,
                last_reviewed_at=None,
            )
            for slug, skill in skills_by_slug.items()
        ]
        summaries.sort(key=lambda s: s.skill_slug)
        edges = [
            SkillGraphEdge(source=prereq, target=slug, relation="prerequisite")
            for slug, skill in skills_by_slug.items()
            for prereq in skill.prerequisite_ids
            if prereq in skills_by_slug
        ]
        return SkillGraphResponse(skills=summaries, edges=edges)

    async def get_recommendations(
        self, user_id: str, now: Optional[datetime] = None, limit: int = 5
    ) -> List[Recommendation]:
        now = now or datetime.now(timezone.utc)
        skills_by_slug, question_skills_by_q = await self._load_taxonomy()
        states = await self.repository.get_states(user_id)

        skill_names = {slug: s.name for slug, s in skills_by_slug.items()}
        prerequisites = {slug: s.prerequisite_ids for slug, s in skills_by_slug.items()}
        question_by_skill: Dict[str, List[str]] = {}
        for question_id, mappings in question_skills_by_q.items():
            for m in mappings:
                question_by_skill.setdefault(m.skill_slug, []).append(question_id)

        return recommend(
            states=states,
            skill_names=skill_names,
            prerequisites=prerequisites,
            question_by_skill=question_by_skill,
            now=now,
            limit=limit,
        )

    async def get_recommended_questions(
        self,
        user_id: str,
        question_loader: Callable[[str], Awaitable[Optional[Question]]],
        limit: int = 5,
        now: Optional[datetime] = None,
    ) -> List[RecommendedQuestion]:
        """Recommendations enriched with the concrete practice question.

        ``question_loader`` resolves a question ID to a full ``Question`` (or
        ``None``). Recommendations whose question cannot be resolved are
        skipped — the response never fabricates practice data.
        """
        recs = await self.get_recommendations(user_id, now=now, limit=limit)
        results: List[RecommendedQuestion] = []
        for rec in recs:
            question_id = rec.suggested_question_id
            if not question_id:
                continue
            question = await question_loader(question_id)
            if question is None:
                continue
            results.append(
                RecommendedQuestion(
                    skill_slug=rec.skill_slug,
                    skill_name=rec.name,
                    reason=rec.reason,
                    reason_text=rec.reason_text,
                    question=question,
                )
            )
        return results

    async def delete_history(self, user_id: str) -> None:
        await self.repository.delete_user_history(user_id)
