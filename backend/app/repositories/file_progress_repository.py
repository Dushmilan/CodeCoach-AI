import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.models.course_schemas import CourseProgress
from app.ports.progress_repository import ProgressRepository


class FileProgressRepository(ProgressRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._progress: Dict[str, CourseProgress] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("items", [])
        for item in data:
            p = CourseProgress(**item)
            key = f"{p.user_id}:{p.course_id}"
            self._progress[key] = p

    def _save(self):
        items = [p.model_dump() for p in self._progress.values()]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"items": items}, f, indent=2, default=str)

    def _key(self, user_id: str, course_id: str) -> str:
        return f"{user_id}:{course_id}"

    async def get_progress(
        self, user_id: str, course_id: str
    ) -> Optional[CourseProgress]:
        return self._progress.get(self._key(user_id, course_id))

    async def get_all_progress(self, user_id: str) -> List[CourseProgress]:
        return [p for key, p in self._progress.items() if key.startswith(f"{user_id}:")]

    async def mark_lesson_complete(
        self, user_id: str, course_id: str, lesson_id: str
    ) -> CourseProgress:
        key = self._key(user_id, course_id)
        progress = self._progress.get(key)
        if progress is None:
            progress = CourseProgress(
                user_id=user_id,
                course_id=course_id,
                completed_lessons=[],
            )
            self._progress[key] = progress
        if lesson_id not in progress.completed_lessons:
            progress.completed_lessons.append(lesson_id)
        progress.last_accessed_lesson_id = lesson_id
        progress.last_accessed_at = datetime.now(timezone.utc)
        self._save()
        return progress

    async def save(self, progress: CourseProgress) -> None:
        key = self._key(progress.user_id, progress.course_id)
        self._progress[key] = progress
        self._save()
