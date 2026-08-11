"""Unit tests for AnimationValidator — the semantic gate on AI animation scripts.

Covers: valid linear search acceptance, index bounds, match/mismatch truthfulness,
unsupported types, missing data, empty/oversized traces, and narration hygiene.
"""

from app.services.animation_validator import (
    AnimationValidator,
    MAX_STEPS,
    MAX_VALUES,
    animation_validator,
)


def _linear_search(values, target, steps):
    return {
        "type": "linear_search",
        "title": "Searching",
        "data": {"values": values, "target": target},
        "steps": steps,
    }


def _compare(index, result, narration="checking"):
    return {
        "operation": "compare",
        "index": index,
        "result": result,
        "narration": narration,
    }


class TestValidScripts:
    def test_valid_linear_search(self):
        script = _linear_search(
            [5, 1, 2, 3, 4, 5],
            4,
            [_compare(0, "mismatch"), _compare(1, "mismatch"), _compare(4, "match")],
        )
        validated, reason = animation_validator.validate(script)
        assert validated is not None
        assert reason == ""

    def test_target_at_first_index(self):
        script = _linear_search([5, 1], 5, [_compare(0, "match")])
        validated, _ = animation_validator.validate(script)
        assert validated is not None

    def test_duplicate_target_values(self):
        script = _linear_search(
            [5, 1, 5, 3],
            5,
            [_compare(0, "match")],
        )
        validated, _ = animation_validator.validate(script)
        assert validated is not None

    def test_compare_without_result_allowed(self):
        script = _linear_search([1, 2], 2, [_compare(0, None)])
        validated, _ = animation_validator.validate(script)
        assert validated is not None

    def test_visit_and_mark_operations_allowed(self):
        script = _linear_search(
            [1, 2, 3],
            3,
            [
                {"operation": "visit", "index": 0, "narration": "visiting"},
                {
                    "operation": "mark",
                    "index": 2,
                    "result": "match",
                    "narration": "mark",
                },
            ],
        )
        validated, _ = animation_validator.validate(script)
        assert validated is not None


class TestRejections:
    def test_unsupported_type(self):
        script = {
            "type": "bubble_sort",
            "data": {"values": [3, 2, 1]},
            "steps": [_compare(0, "mismatch")],
        }
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "Unsupported animation type" in reason

    def test_not_an_object(self):
        validated, reason = animation_validator.validate("linear_search")
        assert validated is None
        assert "not an object" in reason

    def test_missing_values(self):
        script = _linear_search([], 4, [])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "non-empty values" in reason

    def test_too_many_values(self):
        script = _linear_search(
            list(range(MAX_VALUES + 1)), 1, [_compare(0, "mismatch")]
        )
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "Too many values" in reason

    def test_empty_steps(self):
        script = _linear_search([1, 2, 3], 2, [])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "non-empty steps" in reason

    def test_too_many_steps(self):
        steps = [_compare(0, "mismatch")] * (MAX_STEPS + 1)
        script = _linear_search([1], 1, steps)
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "Too many steps" in reason

    def test_out_of_bounds_index(self):
        script = _linear_search([1, 2, 3], 3, [_compare(9, "mismatch")])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "out-of-bounds" in reason

    def test_negative_index(self):
        script = _linear_search([1, 2, 3], 3, [_compare(-1, "mismatch")])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "out-of-bounds" in reason

    def test_match_step_must_equal_target(self):
        script = _linear_search([5, 1, 2, 3, 4, 5], 4, [_compare(0, "match")])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "does not equal target" in reason

    def test_mismatch_step_must_not_equal_target(self):
        script = _linear_search([5, 1, 2, 3, 4, 5], 5, [_compare(0, "mismatch")])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "equals target" in reason

    def test_missing_narration(self):
        script = _linear_search([1, 2], 2, [{"operation": "compare", "index": 0}])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "missing narration" in reason

    def test_narration_too_long(self):
        script = _linear_search(
            [1, 2], 2, [_compare(0, "mismatch", narration="x" * 301)]
        )
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "exceeds 300 chars" in reason

    def test_step_not_an_object(self):
        script = _linear_search([1, 2], 2, ["not-a-step"])
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "not an object" in reason

    def test_invalid_compare_result(self):
        script = _linear_search(
            [1, 2],
            2,
            [
                {
                    "operation": "compare",
                    "index": 0,
                    "result": "banana",
                    "narration": "x",
                }
            ],
        )
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "invalid compare result" in reason

    def test_compare_result_without_index_is_rejected_not_crash(self):
        script = _linear_search(
            [1, 2],
            2,
            [{"operation": "compare", "result": "match", "narration": "x"}],
        )
        validated, reason = animation_validator.validate(script)
        assert validated is None
        assert "missing an index" in reason

    def test_compare_result_without_index_does_not_raise_in_groq(self):
        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": _linear_search(
                [1, 2],
                2,
                [{"operation": "compare", "result": "match", "narration": "x"}],
            ),
        }
        result = GroqService._validate_animation(data)
        assert "animation" not in result
        assert result["summary"] == "Keep coaching"


class TestGroqIntegration:
    def test_invalid_animation_is_dropped(self):
        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": {
                "type": "linear_search",
                "data": {"values": [5], "target": 4},
                "steps": [_compare(0, "match")],
            },
        }
        result = GroqService._validate_animation(data)
        assert "animation" not in result
        assert result["summary"] == "Keep coaching"

    def test_valid_animation_is_kept(self):
        from app.services.groq_service import GroqService

        data = {
            "summary": "Keep coaching",
            "hints": [],
            "animation": _linear_search([4, 1], 4, [_compare(0, "match")]),
        }
        result = GroqService._validate_animation(data)
        assert result["animation"]["type"] == "linear_search"

    def test_animation_absent_is_untouched(self):
        from app.services.groq_service import GroqService

        data = {"summary": "plain", "hints": []}
        result = GroqService._validate_animation(data)
        assert result == data


class TestValidatorInstance:
    def test_module_level_singleton(self):
        assert isinstance(animation_validator, AnimationValidator)
