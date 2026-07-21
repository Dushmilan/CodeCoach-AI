from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple

from app.models.admin_models import QuestionFilter, QuestionImportResult


class QuestionAdminRepository(ABC):
    @abstractmethod
    async def get_question_by_id(
        self, question_id: str
    ) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    async def update_question(
        self, question_id: str, update_data: Dict[str, Any]
    ) -> bool: ...

    @abstractmethod
    async def delete_question(self, question_id: str) -> bool: ...

    @abstractmethod
    async def list_questions(
        self, filter: QuestionFilter
    ) -> Tuple[List[Dict[str, Any]], int]: ...

    @abstractmethod
    async def import_questions(
        self, questions: List[Dict[str, Any]], dry_run: bool = False
    ) -> QuestionImportResult: ...

    @abstractmethod
    async def create_question(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
