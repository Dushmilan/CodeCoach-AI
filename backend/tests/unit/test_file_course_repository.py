import pytest
import os
import json
import tempfile
from app.repositories.file_course_repository import FileCourseRepository
from app.models.course_schemas import Course

@pytest.mark.asyncio
async def test_load_with_malformed_item():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create course.json with one valid and one malformed item
        data = {
            "items": [
                {"id": "valid-1", "title": "Valid Course", "description": "...", "language": "python", "order": 1, "modules": []},
                {"id": "invalid-1", "title": "Invalid Course"}, # Missing required fields
            ]
        }
        os.makedirs(os.path.join(tmpdir, "python-fundamentals"))
        with open(os.path.join(tmpdir, "python-fundamentals", "course.json"), "w") as f:
            json.dump(data, f)
            
        repo = FileCourseRepository(tmpdir)
        courses = await repo.get_all_courses()
        assert len(courses) == 1
        assert courses[0].id == "valid-1"

@pytest.mark.asyncio
async def test_load_file_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileCourseRepository(tmpdir)
        courses = await repo.get_all_courses()
        assert len(courses) == 0

@pytest.mark.asyncio
async def test_load_file_single_item():
    with tempfile.TemporaryDirectory() as tmpdir:
        data = {"id": "valid-1", "title": "Valid Course", "description": "...", "language": "python", "order": 1, "modules": []}
        os.makedirs(os.path.join(tmpdir, "python-fundamentals"))
        with open(os.path.join(tmpdir, "python-fundamentals", "course.json"), "w") as f:
            json.dump(data, f)
            
        repo = FileCourseRepository(tmpdir)
        courses = await repo.get_all_courses()
        assert len(courses) == 1
        assert courses[0].id == "valid-1"
