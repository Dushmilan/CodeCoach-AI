import json
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from app.models.admin_models import QuestionFilter, QuestionImportResult
from app.ports.question_admin_repository import QuestionAdminRepository

logger = logging.getLogger(__name__)


class FileQuestionAdminRepository(QuestionAdminRepository):
    def __init__(self, questions_file: str = ""):
        self._questions_file = Path(
            questions_file
            or str(
                Path(__file__).resolve().parent.parent.parent
                / "questions"
                / "sample_questions.json"
            )
        )

    def _load_questions(self) -> List[Dict[str, Any]]:
        if not self._questions_file.exists():
            return []
        with open(self._questions_file, encoding="utf-8") as f:
            return json.load(f)

    def _save_questions(self, questions: List[Dict[str, Any]]):
        self._questions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._questions_file, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2)

    async def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        for q in self._load_questions():
            if q.get("id") == question_id:
                return q
        return None

    async def update_question(
        self, question_id: str, update_data: Dict[str, Any]
    ) -> bool:
        questions = self._load_questions()
        for q in questions:
            if q["id"] == question_id:
                q.update(update_data)
                self._save_questions(questions)
                return True
        return False

    async def delete_question(self, question_id: str) -> bool:
        questions = self._load_questions()
        for i, q in enumerate(questions):
            if q["id"] == question_id:
                questions.pop(i)
                self._save_questions(questions)
                return True
        return False

    async def list_questions(
        self, filter: QuestionFilter
    ) -> Tuple[List[Dict[str, Any]], int]:
        all_q = self._load_questions()
        filtered = all_q
        if filter.difficulty:
            filtered = [q for q in filtered if q.get("difficulty") == filter.difficulty]
        if filter.category:
            filtered = [q for q in filtered if q.get("category") == filter.category]
        total = len(filtered)
        start = (filter.page - 1) * filter.per_page
        return filtered[start : start + filter.per_page], total

    async def import_questions(
        self, questions: List[Dict[str, Any]], dry_run: bool = False
    ) -> QuestionImportResult:
        result = QuestionImportResult(
            total=len(questions), successful=0, failed=0, errors=[]
        )
        if dry_run:
            result.successful = len(questions)
            return result
        existing = self._load_questions()
        for q in questions:
            if "id" not in q:
                q["id"] = str(uuid.uuid4())
            existing.append(q)
            result.successful += 1
        self._save_questions(existing)
        return result

    async def create_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
        questions = self._load_questions()
        question = {
            "id": data["id"],
            "title": data["title"],
            "difficulty": data.get("difficulty", "medium"),
            "category": data.get("category", ""),
            "company_tags": data.get("company_tags", []),
            "description": data.get("description", ""),
            "starter_code": data.get(
                "starter_code", {"python": "", "javascript": "", "java": ""}
            ),
            "examples": data.get("examples", []),
            "test_cases": data.get("test_cases", []),
            "hints": data.get("hints", []),
            "solution": data.get("solution", None),
            "time_complexity": data.get("time_complexity", ""),
            "space_complexity": data.get("space_complexity", ""),
            "constraints": data.get("constraints", []),
            "is_interactive": data.get("is_interactive", False),
        }
        questions.append(question)
        self._save_questions(questions)
        return question
