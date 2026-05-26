"""
Tests for the curriculum verification quality gate.
Behavior: Given a synthetic NIM verification response, the script
correctly evaluates lesson quality and marks passing lessons as verified.
"""
import json
import tempfile
from pathlib import Path

import pytest

from scripts.verify_curriculum import (
    evaluate_lesson_quality,
    build_verification_prompt,
    parse_verification_response,
    compute_average_score,
    filter_lessons_by_score,
)


def fake_nim_high_score(prompt: str, api_key: str, model: str) -> str:
    return json.dumps({
        "criteria_scores": {
            "clarity": 95,
            "correctness": 92,
            "pedagogical_value": 90,
        },
        "overall": 92,
        "issues": [],
    })


def fake_nim_low_score(prompt: str, api_key: str, model: str) -> str:
    return json.dumps({
        "criteria_scores": {
            "clarity": 40,
            "correctness": 30,
            "pedagogical_value": 25,
        },
        "overall": 32,
        "issues": ["Content is confusing", "Code examples are incorrect"],
    })


SAMPLE_LESSON = {
    "id": "py-loops-test",
    "course_id": "python-fundamentals",
    "module_id": "python-control-flow",
    "title": "For Loops Practice",
    "type": "exercise",
    "content": "# For Loops\n\nPractice writing for loops.",
    "order": 6,
    "starter_code": "for i in range(5):\n    print(i)",
    "test_cases": [
        {"input": "", "expected_output": "0\n1\n2\n3\n4", "description": "Basic loop"}
    ],
    "language": "python",
}


class TestBuildVerificationPrompt:
    def test_includes_lesson_title_and_content(self):
        prompt = build_verification_prompt(SAMPLE_LESSON)
        assert "For Loops Practice" in prompt
        assert "for loops" in prompt.lower()

    def test_includes_criteria(self):
        prompt = build_verification_prompt(SAMPLE_LESSON)
        assert "clarity" in prompt.lower()
        assert "correctness" in prompt.lower()
        assert "pedagogical" in prompt.lower()


class TestParseVerificationResponse:
    def test_parses_valid_json(self):
        response = fake_nim_high_score("", "", "")
        result = parse_verification_response(response)
        assert result["overall"] == 92
        assert result["criteria_scores"]["clarity"] == 95

    def test_handles_stripped_code_blocks(self):
        response = "```json\n" + fake_nim_high_score("", "", "") + "\n```"
        result = parse_verification_response(response)
        assert result["overall"] == 92

    def test_returns_zero_for_garbage(self):
        result = parse_verification_response("not json at all")
        assert result["overall"] == 0
        assert "Failed to parse" in result["issues"][0]


class TestEvaluateLessonQuality:
    def test_passing_score_survives_threshold(self):
        score, rounds = evaluate_lesson_quality(
            SAMPLE_LESSON,
            fake_nim_high_score,
            api_key="test",
            model="test-model",
            rounds=2,
        )
        assert score > 90
        assert len(rounds) == 2

    def test_low_score_below_threshold(self):
        score, rounds = evaluate_lesson_quality(
            SAMPLE_LESSON,
            fake_nim_low_score,
            api_key="test",
            model="test-model",
            rounds=2,
        )
        assert score < 50
        assert len(rounds) == 2


class TestFilterLessonsByScore:
    def test_passed_above_threshold(self):
        passed, rejected = filter_lessons_by_score(
            [{"id": "a", "_score": 95}, {"id": "b", "_score": 80}],
            threshold=90,
        )
        assert len(passed) == 1
        assert passed[0]["id"] == "a"
        assert len(rejected) == 1
        assert rejected[0]["id"] == "b"
