import json
import logging
import os
from typing import Dict, Optional

from app.models.question_validation_schemas import QuestionValidationStatus
from app.models.schemas import Question, Difficulty
from app.ports.question_repository import QuestionRepository

logger = logging.getLogger(__name__)


class FileQuestionRepository(QuestionRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._questions: Dict[str, Question] = {}
        self._validation_file = os.path.splitext(file_path)[0] + "_validations.json"
        self._validation_statuses: Dict[str, dict] = {}
        self._load()
        self._load_validation_statuses()

    def _load(self):
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("questions", [])
        for item in data:
            try:
                q = Question(**item)
                self._questions[q.id] = q
            except Exception as e:
                title = item.get("title", "unknown")
                logger.warning("Skipping malformed question '%s': %s", title, e)

    def _load_validation_statuses(self):
        if not os.path.exists(self._validation_file):
            return
        with open(self._validation_file, "r", encoding="utf-8") as f:
            self._validation_statuses = json.load(f)

    def _save_validation_statuses(self):
        with open(self._validation_file, "w", encoding="utf-8") as f:
            json.dump(self._validation_statuses, f, indent=2)

    async def get_all(
        self, difficulty: Optional[Difficulty] = None, category: Optional[str] = None
    ) -> list:
        result = list(self._questions.values())
        if difficulty:
            result = [q for q in result if q.difficulty == difficulty]
        if category:
            result = [q for q in result if q.category.lower() == category.lower()]
        return result

    async def get_by_id(self, question_id: str) -> Optional[Question]:
        return self._questions.get(question_id)

    async def search(
        self,
        query: str,
        difficulty: Optional[Difficulty] = None,
        category: Optional[str] = None,
    ) -> list:
        query = query.lower()
        result = [
            q
            for q in self._questions.values()
            if query in q.title.lower() or query in q.description.lower()
        ]
        if difficulty:
            result = [q for q in result if q.difficulty == difficulty]
        if category:
            result = [q for q in result if q.category.lower() == category.lower()]
        return result

    async def get_categories(self) -> list:
        cats = set()
        for q in self._questions.values():
            cats.add(q.category)
        return sorted(cats)

    async def get_company_tags(self) -> list:
        tags = set()
        for q in self._questions.values():
            for tag in q.company_tags:
                tags.add(tag)
        return sorted(tags)

    async def add(self, question: Question) -> None:
        self._questions[question.id] = question

    async def save_validation_status(
        self, question_id: str, status: QuestionValidationStatus
    ) -> None:
        self._validation_statuses[question_id] = {
            "is_validated": status.is_validated,
            "last_validated": status.last_validated.isoformat()
            if status.last_validated
            else None,
            "validation_passed": status.validation_passed,
            "validation_errors": status.validation_errors,
            "validation_warnings": status.validation_warnings,
        }
        self._save_validation_statuses()

    async def get_validation_statuses(self) -> Dict[str, dict]:
        return dict(self._validation_statuses)
