import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.verify_and_populate import (
    build_verification_prompt,
    parse_verification_response,
    compute_average_score,
    filter_questions_by_score,
    merge_with_existing,
    load_existing_questions,
    evaluate_question_quality,
    VERIFICATION_CRITERIA,
)

SAMPLE_QUESTION = {
    "id": "two-sum",
    "title": "Two Sum",
    "difficulty": "easy",
    "category": "Arrays & Hashing",
    "company_tags": ["Google", "Amazon"],
    "description": "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.",
    "starter": {
        "python": "def two_sum(nums: list[int], target: int) -> list[int]:\n    pass",
        "javascript": "function twoSum(nums, target) {\n    \n}",
        "java": "public class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[0];\n    }\n}",
    },
    "examples": [
        {
            "input": "[2,7,11,15], target=9",
            "output": "[0,1]",
            "explanation": "nums[0]+nums[1]=9",
        },
        {
            "input": "[3,2,4], target=6",
            "output": "[1,2]",
            "explanation": "nums[1]+nums[2]=6",
        },
    ],
    "test_cases": [
        {
            "input": "[2,7,11,15], target=9",
            "expected_output": "[0,1]",
            "description": "Basic",
            "hidden": False,
        },
        {
            "input": "[3,2,4], target=6",
            "expected_output": "[1,2]",
            "description": "Random order",
            "hidden": False,
        },
        {
            "input": "[3,3], target=6",
            "expected_output": "[0,1]",
            "description": "Duplicate values",
            "hidden": True,
        },
    ],
    "hints": ["Use a hash map for O(1) lookups", "Store complements as you iterate"],
    "solution": "Use a hash map to store each element's complement.",
    "time_complexity": "O(n)",
    "space_complexity": "O(n)",
    "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9"],
}


class TestBuildVerificationPrompt:
    def test_contains_all_question_fields(self):
        prompt = build_verification_prompt(SAMPLE_QUESTION)
        assert "Two Sum" in prompt
        assert "easy" in prompt
        assert "Arrays & Hashing" in prompt
        assert "return indices" in prompt
        assert "hash map" in prompt
        assert "O(n)" in prompt

    def test_contains_all_eight_criteria(self):
        prompt = build_verification_prompt(SAMPLE_QUESTION)
        for criterion in VERIFICATION_CRITERIA:
            assert criterion in prompt, f"Missing criterion: {criterion}"

    def test_requests_json_response(self):
        prompt = build_verification_prompt(SAMPLE_QUESTION)
        assert "JSON" in prompt

    def test_strict_reviewer_tone(self):
        prompt = build_verification_prompt(SAMPLE_QUESTION)
        assert (
            "strict" in prompt.lower() or "critical" in prompt.lower() or "QA" in prompt
        )


class TestParseVerificationResponse:
    def test_parses_valid_json(self):
        raw = json.dumps(
            {
                "criteria_scores": {
                    "test_cases": 95,
                    "description": 90,
                    "difficulty": 85,
                    "category": 100,
                    "starter_code": 88,
                    "solution": 92,
                    "hints": 80,
                    "constraints": 90,
                },
                "overall": 90,
                "issues": ["Hint 3 is too revealing"],
            }
        )
        result = parse_verification_response(raw)
        assert result["overall"] == 90
        assert result["issues"] == ["Hint 3 is too revealing"]
        assert result["criteria_scores"]["test_cases"] == 95

    def test_handles_code_fence(self):
        raw = '```json\n{"overall": 92, "criteria_scores": {"test_cases": 90, "description": 85, "difficulty": 80, "category": 95, "starter_code": 90, "solution": 95, "hints": 85, "constraints": 90}, "issues": []}\n```'
        result = parse_verification_response(raw)
        assert result["overall"] == 92

    def test_missing_overall_defaults_to_average(self):
        raw = json.dumps(
            {
                "criteria_scores": {
                    "test_cases": 90,
                    "description": 90,
                    "difficulty": 90,
                    "category": 90,
                    "starter_code": 90,
                    "solution": 90,
                    "hints": 90,
                    "constraints": 90,
                },
                "issues": [],
            }
        )
        result = parse_verification_response(raw)
        assert result["overall"] == 90

    def test_malformed_json_returns_zero(self):
        result = parse_verification_response("This is not JSON")
        assert result["overall"] == 0
        assert result["issues"] == ["Failed to parse AI response"]

    def test_partial_criteria_scores_defaults_to_zero(self):
        raw = json.dumps(
            {
                "criteria_scores": {"test_cases": 90},
                "overall": 50,
                "issues": [],
            }
        )
        result = parse_verification_response(raw)
        assert result["criteria_scores"]["description"] == 0

    def test_extracts_json_from_freeform_text(self):
        raw = 'Here is my evaluation:\n\n{"overall": 88, "criteria_scores": {"test_cases": 90, "description": 85, "difficulty": 80, "category": 95, "starter_code": 90, "solution": 95, "hints": 85, "constraints": 90}, "issues": ["Minor hint issue"]}'
        result = parse_verification_response(raw)
        assert result["overall"] == 88


class TestComputeAverageScore:
    def test_averages_multiple_rounds(self):
        rounds = [{"overall": 90}, {"overall": 92}, {"overall": 88}, {"overall": 94}]
        avg = compute_average_score(rounds)
        assert avg == 91.0

    def test_single_round(self):
        rounds = [{"overall": 85}]
        avg = compute_average_score(rounds)
        assert avg == 85.0

    def test_empty_rounds_returns_zero(self):
        avg = compute_average_score([])
        assert avg == 0.0

    def test_handles_float_precision(self):
        rounds = [{"overall": 90}, {"overall": 91}, {"overall": 92}]
        avg = compute_average_score(rounds)
        assert avg == 91.0


class TestFilterQuestionsByScore:
    def test_filters_above_threshold(self):
        questions = [
            {"id": "a", "title": "A", "_score": 95},
            {"id": "b", "title": "B", "_score": 80},
            {"id": "c", "title": "C", "_score": 91},
        ]
        passed, rejected = filter_questions_by_score(questions, threshold=90)
        assert len(passed) == 2
        assert passed[0]["id"] == "a"
        assert passed[1]["id"] == "c"
        assert len(rejected) == 1
        assert rejected[0]["id"] == "b"

    def test_boundary_threshold(self):
        questions = [{"id": "a", "title": "A", "_score": 90}]
        passed, rejected = filter_questions_by_score(questions, threshold=90)
        assert len(passed) == 0
        assert len(rejected) == 1

    def test_scores_above_90_inclusive(self):
        questions = [{"id": "a", "title": "A", "_score": 90.01}]
        passed, rejected = filter_questions_by_score(questions, threshold=90)
        assert len(passed) == 1

    def test_empty_list(self):
        passed, rejected = filter_questions_by_score([], threshold=90)
        assert passed == []
        assert rejected == []


class TestMergeWithExisting:
    def test_merges_new_questions_with_existing(self):
        existing = [{"id": "existing-1", "title": "Existing"}]
        new = [{"id": "new-1", "title": "New One"}]
        merged = merge_with_existing(existing, new)
        assert len(merged) == 2
        ids = [q["id"] for q in merged]
        assert "existing-1" in ids
        assert "new-1" in ids

    def test_handles_id_collisions(self):
        existing = [{"id": "collision", "title": "Original"}]
        new = [{"id": "collision", "title": "Duplicate"}]
        merged = merge_with_existing(existing, new)
        assert len(merged) == 2
        ids = [q["id"] for q in merged]
        assert "collision" in ids
        assert any("collision-" in q["id"] for q in merged if q["title"] == "Duplicate")

    def test_preserves_existing_order(self):
        existing = [{"id": "a", "title": "A"}, {"id": "b", "title": "B"}]
        new = [{"id": "c", "title": "C"}]
        merged = merge_with_existing(existing, new)
        assert merged[0]["id"] == "a"
        assert merged[1]["id"] == "b"
        assert merged[2]["id"] == "c"


class TestLoadExistingQuestions:
    def test_loads_wrapped_format(self, tmp_path):
        f = tmp_path / "questions.json"
        f.write_text(json.dumps({"questions": [{"id": "q1", "title": "Q1"}]}))
        questions = load_existing_questions(str(f))
        assert len(questions) == 1
        assert questions[0]["id"] == "q1"

    def test_loads_array_format(self, tmp_path):
        f = tmp_path / "questions.json"
        f.write_text(json.dumps([{"id": "q1", "title": "Q1"}]))
        questions = load_existing_questions(str(f))
        assert len(questions) == 1
        assert questions[0]["id"] == "q1"

    def test_returns_empty_for_missing_file(self, tmp_path):
        questions = load_existing_questions(str(tmp_path / "nonexistent.json"))
        assert questions == []

    def test_returns_empty_for_empty_file(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("{}")
        questions = load_existing_questions(str(f))
        assert questions == []


class TestEvaluateQuestionQuality:
    def test_returns_score_and_rounds(self):
        def mock_call_nvidia(prompt, api_key, model):
            return json.dumps(
                {
                    "overall": 92,
                    "criteria_scores": {
                        "test_cases": 90,
                        "description": 95,
                        "difficulty": 85,
                        "category": 95,
                        "starter_code": 90,
                        "solution": 95,
                        "hints": 88,
                        "constraints": 92,
                    },
                    "issues": [],
                }
            )

        score, rounds = evaluate_question_quality(
            SAMPLE_QUESTION, mock_call_nvidia, "test-key", "test-model", rounds=3
        )
        assert score == 92.0
        assert len(rounds) == 3
        for r in rounds:
            assert r["overall"] == 92

    def test_handles_api_failures(self):
        call_count = 0

        def mock_call_nvidia(prompt, api_key, model):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None
            return json.dumps(
                {
                    "overall": 90,
                    "criteria_scores": {
                        "test_cases": 90,
                        "description": 90,
                        "difficulty": 90,
                        "category": 90,
                        "starter_code": 90,
                        "solution": 90,
                        "hints": 90,
                        "constraints": 90,
                    },
                    "issues": [],
                }
            )

        score, rounds = evaluate_question_quality(
            SAMPLE_QUESTION, mock_call_nvidia, "test-key", "test-model", rounds=2
        )
        assert score == 90.0
        assert len(rounds) == 1

    def test_returns_zero_on_all_failures(self):
        def mock_call_nvidia(prompt, api_key, model):
            return None

        score, rounds = evaluate_question_quality(
            SAMPLE_QUESTION, mock_call_nvidia, "test-key", "test-model", rounds=2
        )
        assert score == 0.0
        assert rounds == []
