"""Tests for the 100-question bank (backend/questions/sample_questions.json).

These are pure-data tests: they validate the bank structure, schema validity,
difficulty/category distribution, uniqueness, and that every test case's
expected output is consistent with the reference solution used by the builder.
"""

import json
import copy
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from question_bank import ALL_SPECS
from question_bank.build_bank import _encode, _encode_input, _expected_from

BASE_DIR = Path(__file__).resolve().parent.parent.parent
QUESTIONS_PATH = BASE_DIR / "questions" / "sample_questions.json"

TARGET_DIFFICULTY = {"easy": 30, "medium": 50, "hard": 20}
TARGET_TOTAL = 100
CURRICULUM_LINKED_IDS = {
    "c9d1a3f2-5b6e-4a7f-8c0d-1e2f3a4b5c6d",
    "f7e2d4a1-3b5c-4d6e-8f9a-0b1c2d3e4f5a",
    "7b9d2c1a-3e4f-5a6b-7c8d-9e0f1a2b3c4d",
}


def _load_bank():
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return data.get("questions", data) if isinstance(data, dict) else data


class TestQuestionBankStructure:
    def test_bank_has_exactly_100_questions(self):
        assert len(_load_bank()) == TARGET_TOTAL

    def test_specs_match_generated_bank(self):
        bank = _load_bank()
        spec_ids = {s.id for s in ALL_SPECS}
        assert {q["id"] for q in bank} == spec_ids
        assert len(spec_ids) == TARGET_TOTAL

    def test_all_ids_unique(self):
        ids = [q["id"] for q in _load_bank()]
        assert len(ids) == len(set(ids))

    def test_difficulty_distribution(self):
        counts = Counter(q["difficulty"] for q in _load_bank())
        assert dict(counts) == TARGET_DIFFICULTY

    def test_every_difficulty_valid(self):
        from app.models.schemas import Difficulty

        for q in _load_bank():
            assert q["difficulty"] in Difficulty._value2member_map_

    def test_category_distribution_reasonable(self):
        counts = Counter(q["category"] for q in _load_bank())
        assert len(counts) >= 10
        assert max(counts.values()) <= 15

    def test_curriculum_linked_ids_present(self):
        ids = {q["id"] for q in _load_bank()}
        assert CURRICULUM_LINKED_IDS.issubset(ids)

    def test_standard_ids_preserved_for_progress_continuity(self):
        ids = {q["id"] for q in _load_bank()}
        standard = {
            "three-sum",
            "product-of-array-except-self",
            "subarray-sum-equals-k",
            "find-first-and-last-position-in-sorted-array",
            "rotate-image",
            "merge-intervals",
            "next-permutation",
            "maximum-product-subarray",
            "find-all-duplicates-in-an-array",
            "contiguous-array",
        }
        assert standard.issubset(ids)

    def test_every_question_has_company_tags(self):
        for q in _load_bank():
            assert q["company_tags"], q["id"]

    def test_every_question_has_minimum_test_cases(self):
        for q in _load_bank():
            assert len(q["test_cases"]) >= 6, q["id"]
            hidden = sum(1 for tc in q["test_cases"] if tc["hidden"])
            assert hidden >= 2, q["id"]

    def test_every_question_has_examples_hints_solution_complexity(self):
        for q in _load_bank():
            assert q["examples"], q["id"]
            assert q["hints"], q["id"]
            assert q["solution"], q["id"]
            assert q["time_complexity"], q["id"]
            assert q["space_complexity"], q["id"]
            assert q["constraints"], q["id"]

    def test_every_question_has_starter_for_three_languages(self):
        for q in _load_bank():
            for lang in ("python", "javascript", "java"):
                assert q["starter"].get(lang), (q["id"], lang)

    def test_every_question_parses_as_schema(self):
        from app.models.schemas import Question

        for item in _load_bank():
            q = Question(**item)
            assert q.id == item["id"]
            assert q.starter.python
            assert q.test_cases


class TestQuestionBankDataIntegrity:
    def test_expected_outputs_match_reference_solutions(self):
        fails = []
        for spec in ALL_SPECS:
            for args, _ in spec.tests:
                args_copy = copy.deepcopy(args)
                expected = _expected_from(spec.ref, args_copy)
                input_str = _encode_input(args_copy)
                # Re-run the reference against the parsed input (runner-style)
                parsed = _runner_parse_args(input_str)
                actual = _runner_serialize(spec.ref(*copy.deepcopy(parsed)), parsed)
                if not _outputs_match(actual, expected):
                    fails.append((spec.id, input_str, actual, expected))
        assert not fails, f"{len(fails)} mismatches: {fails[:5]}"

    def test_all_spec_tests_serialize(self):
        """Every spec test must serialize to a non-empty input line."""
        for spec in ALL_SPECS:
            for args, _ in spec.tests:
                assert _encode_input(args), spec.id
                assert _encode(args[0]) != "", spec.id


def _runner_parse_args(input_str):
    lines = input_str.split("\n") if input_str else [""]
    if len(lines) == 1:
        try:
            return [json.loads(lines[0])]
        except Exception:
            return [lines[0]]
    elif len(lines) == 2:
        try:
            a = json.loads(lines[0])
        except Exception:
            a = lines[0]
        try:
            b = json.loads(lines[1])
        except Exception:
            b = lines[1]
        return [a, b]
    return [json.loads(ln) if ln.strip() else ln for ln in lines]


def _runner_serialize(result, parsed):
    in_val = parsed[0] if parsed else None
    if result is None and isinstance(in_val, (list, dict)):
        return json.dumps(in_val, separators=(",", ":"))
    if isinstance(result, list):
        return json.dumps(result, separators=(",", ":"))
    if isinstance(result, bool):
        return str(result).lower()
    if isinstance(result, str):
        return result
    return str(result)


def _outputs_match(actual, expected):
    if actual.endswith("\n"):
        actual = actual[:-1]
    try:
        decoded_expected = json.loads(expected)
    except Exception:
        decoded_expected = None
    try:
        decoded_actual = json.loads(actual)
    except Exception:
        decoded_actual = None
    if isinstance(decoded_expected, str):
        return actual == decoded_expected or decoded_actual == decoded_expected
    if decoded_expected is not None:
        return decoded_actual == decoded_expected
    if isinstance(decoded_actual, str):
        return actual == expected or decoded_actual == expected
    return actual == expected
