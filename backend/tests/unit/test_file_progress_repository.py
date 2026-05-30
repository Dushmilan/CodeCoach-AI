import pytest
import os
import json
import tempfile
from app.repositories.file_progress_repository import FileProgressRepository
from app.models.course_schemas import CourseProgress

@pytest.mark.asyncio
async def test_progress_repository_load_and_save():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "items": [
                {
                    "user_id": "u1",
                    "course_id": "c1",
                    "completed_lessons": ["l1"],
                    "last_accessed_lesson_id": "l1"
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name
    
    try:
        repo = FileProgressRepository(temp_path)
        progress = await repo.get_progress("u1", "c1")
        assert progress is not None
        assert progress.completed_lessons == ["l1"]
        
        # Test save
        progress.completed_lessons.append("l2")
        await repo.save(progress)
        
        # Verify save
        repo2 = FileProgressRepository(temp_path)
        progress2 = await repo2.get_progress("u1", "c1")
        assert progress2 is not None
        assert "l2" in progress2.completed_lessons
        
    finally:
        os.unlink(temp_path)

@pytest.mark.asyncio
async def test_mark_lesson_complete():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"items": []}, f)
        temp_path = f.name
    
    try:
        repo = FileProgressRepository(temp_path)
        await repo.mark_lesson_complete("u1", "c1", "l1")
        progress = await repo.get_progress("u1", "c1")
        assert progress is not None
        assert "l1" in progress.completed_lessons
    finally:
        os.unlink(temp_path)
