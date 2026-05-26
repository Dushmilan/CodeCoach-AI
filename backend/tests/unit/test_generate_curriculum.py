"""
Tests for the curriculum generation script.
Behavior: Given a synthetic NIM API response, the script writes valid Lesson JSON.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.generate_curriculum import generate_lessons


SAMPLE_NIM_RESPONSE = json.dumps([
    {
        "id": "py-variables-exercise-1",
        "course_id": "python-fundamentals",
        "module_id": "python-intro",
        "title": "Variable Assignment Practice",
        "type": "exercise",
        "content": "# Variable Assignment\n\nPractice assigning values to variables.",
        "order": 4,
        "starter_code": "name = input()\n",
        "test_cases": [
            {"input": "Alice", "expected_output": "Hello, Alice!", "description": "Greet Alice"}
        ],
        "language": "python"
    },
    {
        "id": "py-data-types",
        "course_id": "python-fundamentals",
        "module_id": "python-intro",
        "title": "Data Types Explained",
        "type": "theory",
        "content": "# Data Types\n\nLearn about int, float, str, bool.",
        "order": 5,
        "language": "python"
    }
])


def fake_nim_call(prompt: str, api_key: str, model: str) -> str:
    return SAMPLE_NIM_RESPONSE


def fake_nim_call_invalid(prompt: str, api_key: str, model: str) -> str:
    return "this is not valid json"


class TestGenerateLessons:
    def test_writes_valid_lesson_json_to_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            lessons = generate_lessons(
                language="python",
                count=2,
                output_dir=output_dir,
                api_key="test-key",
                _call_nim=fake_nim_call,
            )

            assert len(lessons) == 2
            assert lessons[0]["id"] == "py-variables-exercise-1"
            assert lessons[0]["type"] == "exercise"
            assert lessons[0]["language"] == "python"

            lessons_file = output_dir / "lessons.json"
            assert lessons_file.exists()
            with open(lessons_file) as f:
                data = json.load(f)
            items = data.get("items", data)
            assert len(items) >= 2
            written = {item["id"] for item in items}
            assert "py-variables-exercise-1" in written

    def test_handles_malformed_api_response(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            with pytest.raises(ValueError, match="Failed to parse"):
                generate_lessons(
                    language="python",
                    count=1,
                    output_dir=output_dir,
                    api_key="test-key",
                    _call_nim=fake_nim_call_invalid,
                )
