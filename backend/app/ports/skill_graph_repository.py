from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.models.skill_graph_schemas import (
    LearningEvent,
    QuestionSkill,
    Skill,
    UserSkillState,
)


class SkillGraphRepository(ABC):
    """Persistence port for the Personal Skill Graph.

    Implementations must scope reads and writes strictly to a single user.
    """

    @abstractmethod
    async def list_skills(self) -> List[Skill]: ...

    @abstractmethod
    async def get_question_skills(self) -> List[QuestionSkill]: ...

    @abstractmethod
    async def event_exists(self, event_id: str) -> bool: ...

    @abstractmethod
    async def save_event(self, event: LearningEvent) -> None: ...

    @abstractmethod
    async def get_user_events(
        self, user_id: str, since: Optional[object] = None
    ) -> List[LearningEvent]: ...

    @abstractmethod
    async def get_states(self, user_id: str) -> Dict[str, UserSkillState]: ...

    @abstractmethod
    async def save_state(self, state: UserSkillState) -> None: ...

    @abstractmethod
    async def delete_user_history(self, user_id: str) -> None: ...
