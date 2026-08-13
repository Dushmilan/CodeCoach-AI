"""In-memory SkillGraphRepository for local simulation and tests.

This is NOT a production store — the AGENTS.md rules require runtime
repositories to be SQL against Supabase. This fake exists so the deterministic
engine and the learner-profile simulation can run locally without a database.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.models.skill_graph_schemas import (
    LearningEvent,
    QuestionSkill,
    Skill,
    UserSkillState,
)
from app.ports.skill_graph_repository import SkillGraphRepository


class InMemorySkillGraphRepository(SkillGraphRepository):
    def __init__(self):
        self._skills: List[Skill] = []
        self._question_skills: List[QuestionSkill] = []
        self._events: Dict[str, LearningEvent] = {}
        self._events_by_user: Dict[str, List[LearningEvent]] = {}
        self._states: Dict[str, Dict[str, UserSkillState]] = {}

    def seed_skills(self, skills: List[Skill]) -> None:
        self._skills = list(skills)

    def seed_question_skills(self, question_skills: List[QuestionSkill]) -> None:
        self._question_skills = list(question_skills)

    async def list_skills(self) -> List[Skill]:
        return list(self._skills)

    async def get_question_skills(self) -> List[QuestionSkill]:
        return list(self._question_skills)

    async def event_exists(self, event_id: str) -> bool:
        return event_id in self._events

    async def save_event(self, event: LearningEvent) -> None:
        self._events[event.id] = event
        self._events_by_user.setdefault(event.user_id, []).append(event)

    async def get_user_events(
        self, user_id: str, since: Optional[object] = None
    ) -> List[LearningEvent]:
        events = self._events_by_user.get(user_id, [])
        if since is not None:
            events = [e for e in events if e.occurred_at >= since]
        return sorted(events, key=lambda e: e.occurred_at)

    async def get_states(self, user_id: str) -> Dict[str, UserSkillState]:
        return dict(self._states.get(user_id, {}))

    async def save_state(self, state: UserSkillState) -> None:
        self._states.setdefault(state.user_id, {})[state.skill_slug] = state

    async def delete_user_history(self, user_id: str) -> None:
        self._events = {k: v for k, v in self._events.items() if v.user_id != user_id}
        self._events_by_user.pop(user_id, None)
        self._states.pop(user_id, None)
