import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.generate_questions import (
    parse_questions, build_prompt, slugify, pre_validate_question,
    save_checkpoint, load_checkpoint, CHECKPOINT_FILE,
    VALID_TOPICS_SET, TOPICS,
)


class TestPreValidate:
    def test_valid_question_passes(self):
        q = {
            "title": "Two Sum",
            "description": "Given an array of integers nums and an integer target, return indices of the two numbers that add up to target. You may assume that each input would have exactly one solution, and you may not use the same element twice. You can return the answer in any order.",
            "difficulty": "easy",
            "category": "Arrays & Hashing",
            "starter": {
                "python": "def two_sum(nums, target): pass",
                "javascript": "function twoSum(nums, target) {}",
                "java": "class Solution { public int[] twoSum(int[] nums, int target) { return new int[0]; } }",
            },
            "test_cases": [{"input": "x", "expected_output": "y", "description": "t", "hidden": True} for _ in range(12)],
            "solution": "Use a hash map to store complements.",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9"],
        }
        assert pre_validate_question(q, "Arrays & Hashing") is None

    def test_missing_title(self):
        q = {"description": "x" * 101, "difficulty": "easy", "category": "Arrays & Hashing", "starter": {}, "test_cases": []}
        err = pre_validate_question(q, "Arrays & Hashing")
        assert err is not None
        assert "title" in err.lower()

    def test_description_too_short(self):
        q = {"title": "Test", "description": "short", "difficulty": "easy", "category": "Arrays & Hashing", "starter": {}, "test_cases": []}
        err = pre_validate_question(q, "Arrays & Hashing")
        assert err is not None
        assert "description" in err.lower()

    def test_category_mismatch(self):
        q = {
            "title": "Test", "description": "x" * 101, "difficulty": "easy",
            "category": "Wrong Category", "starter": {"python": "x", "javascript": "x", "java": "x"},
            "test_cases": [{"input": "x", "expected_output": "y", "description": "t", "hidden": True} for _ in range(12)],
            "solution": "x", "time_complexity": "O(1)", "space_complexity": "O(1)",
            "constraints": ["a", "b", "c"],
        }
        err = pre_validate_question(q, "Arrays & Hashing")
        assert err is not None
        assert "category" in err.lower()

    def test_wrong_number_of_test_cases(self):
        q = {
            "title": "Test", "description": "x" * 101, "difficulty": "easy",
            "category": "Arrays & Hashing", "starter": {"python": "x", "javascript": "x", "java": "x"},
            "test_cases": [{"input": "x", "expected_output": "y", "description": "t", "hidden": True} for _ in range(5)],
            "solution": "x", "time_complexity": "O(1)", "space_complexity": "O(1)",
            "constraints": ["a", "b", "c"],
        }
        err = pre_validate_question(q, "Arrays & Hashing")
        assert err is not None
        assert "12" in err

    def test_no_hidden_test_cases(self):
        q = {
            "title": "Test", "description": "x" * 101, "difficulty": "easy",
            "category": "Arrays & Hashing", "starter": {"python": "x", "javascript": "x", "java": "x"},
            "test_cases": [{"input": "x", "expected_output": "y", "description": "t", "hidden": False} for _ in range(12)],
            "solution": "x", "time_complexity": "O(1)", "space_complexity": "O(1)",
            "constraints": ["a", "b", "c"],
        }
        err = pre_validate_question(q, "Arrays & Hashing")
        assert err is not None
        assert "hidden" in err.lower()

    def test_missing_starter_code(self):
        q = {
            "title": "Test", "description": "x" * 101, "difficulty": "easy",
            "category": "Arrays & Hashing", "starter": {"python": "x"},
            "test_cases": [{"input": "x", "expected_output": "y", "description": "t", "hidden": True} for _ in range(12)],
            "solution": "x", "time_complexity": "O(1)", "space_complexity": "O(1)",
            "constraints": ["a", "b", "c"],
        }
        err = pre_validate_question(q, "Arrays & Hashing")
        assert err is not None
        assert "starter" in err.lower() or "java" in err.lower()

    def test_missing_solution(self):
        q = {
            "title": "Test", "description": "x" * 101, "difficulty": "easy",
            "category": "Arrays & Hashing", "starter": {"python": "x", "javascript": "x", "java": "x"},
            "test_cases": [{"input": "x", "expected_output": "y", "description": "t", "hidden": True} for _ in range(12)],
            "time_complexity": "O(1)", "space_complexity": "O(1)",
            "constraints": ["a", "b", "c"],
        }
        err = pre_validate_question(q, "Arrays & Hashing")
        assert err is not None
        assert "solution" in err.lower()


class TestCheckpoint:
    def test_save_and_load_checkpoint(self, tmp_path):
        import json
        from scripts.generate_questions import CHECKPOINT_FILE
        original = CHECKPOINT_FILE
        tmp_checkpoint = os.path.join(tmp_path, "checkpoint.json")
        import scripts.generate_questions as gen_mod
        gen_mod.CHECKPOINT_FILE = tmp_checkpoint
        try:
            state = {"questions": [{"title": "Q1"}], "total": 1, "completed_labels": ["test"]}
            from scripts.generate_questions import save_checkpoint, load_checkpoint
            save_checkpoint(state)
            loaded = load_checkpoint()
            assert loaded is not None
            assert loaded["total"] == 1
            assert len(loaded["questions"]) == 1
            assert "test" in loaded["completed_labels"]
        finally:
            gen_mod.CHECKPOINT_FILE = original


class TestSlugify:
    def test_basic_slug(self):
        assert slugify("Two Sum Problem") == "two-sum-problem"

    def test_special_chars_removed(self):
        assert slugify("Hello, World! (easy)") == "hello-world-easy"

    def test_handles_duplicates(self):
        from scripts.generate_questions import EXISTING_IDS

        EXISTING_IDS.add("test")
        result = slugify("test")
        assert result == "test-2"


class TestBuildPrompt:
    def test_contains_topic_and_difficulty(self):
        prompt = build_prompt("Arrays", "easy", 3)
        assert "Arrays" in prompt
        assert "easy" in prompt
        assert "3" in prompt

    def test_requests_json_array(self):
        prompt = build_prompt("Graphs", "hard", 2)
        assert "JSON array" in prompt

    def test_classic_archetype_has_traditional_framing(self):
        prompt = build_prompt("Arrays", "easy", 1, archetype="classic")
        assert "classic coding interview" in prompt
        assert "Return ONLY the JSON array" in prompt
        assert "EXACTLY 12" in prompt or "12 test" in prompt

    def test_creative_archetype_has_scenario_seed(self):
        prompt = build_prompt("Sliding Window", "medium", 1, archetype="creative_2026")
        assert "LLM context window" in prompt or "real-world" in prompt
        assert "FRAME THE PROBLEM" in prompt

    def test_creative_archetype_falls_back_for_unknown_topic(self):
        prompt = build_prompt("Unknown Topic", "easy", 1, archetype="creative_2026")
        assert "modern real-world" in prompt

    def test_classic_enforces_category(self):
        prompt = build_prompt("Binary Search", "medium", 1, archetype="classic")
        assert 'MUST be exactly' in prompt
        assert '"Binary Search"' in prompt or "Binary Search" in prompt

    def test_creative_enforces_category(self):
        prompt = build_prompt("Graphs", "hard", 1, archetype="creative_2026")
        assert "CRITICAL RULE" in prompt or 'MUST be exactly' in prompt

    def test_classic_has_difficulty_calibration(self):
        prompt = build_prompt("Linked List", "hard", 1, archetype="classic")
        assert "Median of Two Sorted Arrays" in prompt
        assert "Calibration" in prompt

    def test_classic_easy_has_easy_calibration(self):
        prompt = build_prompt("Stack", "easy", 1, archetype="classic")
        assert "Two Sum" in prompt
        assert "Calibration" in prompt

    def test_creative_has_difficulty_calibration(self):
        prompt = build_prompt("Trees", "medium", 1, archetype="creative_2026")
        assert "Calibration" in prompt
        assert "Longest Substring" in prompt


class TestParseQuestions:
    def test_parses_valid_json_array(self):
        raw = json.dumps(
            [
                {
                    "title": "Find Max in Array",
                    "description": "Given an array, find the maximum element.",
                    "difficulty": "easy",
                    "category": "Arrays",
                    "examples": [
                        {"input": "[1,2,3]", "output": "3", "explanation": "3 is max"}
                    ],
                    "test_cases": [
                        {
                            "input": "[1,2,3]",
                            "expected_output": "3",
                            "description": "basic",
                            "hidden": False,
                        }
                    ],
                }
            ]
        )
        result = parse_questions(raw)
        assert len(result) == 1
        assert result[0]["id"] == "find-max-in-array"
        assert "starter" in result[0]
        assert result[0]["company_tags"] == []

    def test_parses_code_block(self):
        raw = '```json\n[{"title": "Test", "description": "Desc", "difficulty": "medium", "category": "Test"}]\n```'
        result = parse_questions(raw)
        assert len(result) == 1

    def test_skips_malformed(self):
        raw = json.dumps([{"title": "Good", "description": "Yes"}, {"bad": "object"}])
        result = parse_questions(raw)
        assert len(result) == 1
        assert result[0]["title"] == "Good"

    def test_extracts_json_from_freeform_text(self):
        raw = 'Here are the questions:\n\n[{"title": "Found", "description": "Desc", "difficulty": "hard", "category": "Test"}]\n\nHope that helps!'
        result = parse_questions(raw)
        assert len(result) == 1
        assert result[0]["title"] == "Found"

    def test_returns_empty_for_no_json(self):
        result = parse_questions("No JSON here at all")
        assert result == []
