import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.generate_questions import parse_questions, build_prompt, slugify


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
        assert "EXACTLY 20" in prompt or "20 test" in prompt

    def test_creative_archetype_has_scenario_seed(self):
        prompt = build_prompt("Sliding Window", "medium", 1, archetype="creative_2026")
        assert "LLM context window" in prompt or "real-world" in prompt
        assert "FRAME THE PROBLEM" in prompt

    def test_creative_archetype_falls_back_for_unknown_topic(self):
        prompt = build_prompt("Unknown Topic", "easy", 1, archetype="creative_2026")
        assert "modern real-world" in prompt


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
