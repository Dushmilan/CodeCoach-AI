import json
import os
from typing import Optional

from app.models.schemas import Question, Difficulty
from app.ports.question_repository import QuestionRepository


class FileQuestionRepository(QuestionRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._questions: dict[str, Question] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("questions", [])
        for item in data:
            q = Question(**item)
            self._questions[q.id] = q

    async def get_all(self, difficulty: Optional[Difficulty] = None, category: Optional[str] = None) -> list[Question]:
        result = list(self._questions.values())
        if difficulty:
            result = [q for q in result if q.difficulty == difficulty]
        if category:
            result = [q for q in result if q.category.lower() == category.lower()]
        return result

    async def get_by_id(self, question_id: str) -> Optional[Question]:
        return self._questions.get(question_id)

    async def search(self, query: str, difficulty: Optional[Difficulty] = None, category: Optional[str] = None) -> list[Question]:
        query = query.lower()
        result = [
            q for q in self._questions.values()
            if query in q.title.lower() or query in q.description.lower()
        ]
        if difficulty:
            result = [q for q in result if q.difficulty == difficulty]
        if category:
            result = [q for q in result if q.category.lower() == category.lower()]
        return result

    async def get_categories(self) -> list[str]:
        cats = set()
        for q in self._questions.values():
            cats.add(q.category)
        return sorted(cats)

    async def get_company_tags(self) -> list[str]:
        tags = set()
        for q in self._questions.values():
            for tag in q.company_tags:
                tags.add(tag)
        return sorted(tags)

    async def add(self, question: Question) -> None:
        self._questions[question.id] = question
