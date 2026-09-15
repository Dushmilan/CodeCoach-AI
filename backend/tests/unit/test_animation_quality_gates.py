"""Animation quality gates (A4): lint checks + corpus gates over fixtures.

The lint unit test pins the non-blocking `lint_quality` contract (camera,
badge, duplicate narration). The service-level gates build animations with
fake executors — no Piston, no network — and assert zero quality warnings:

- `test_corpus_gate_zero_quality_warnings`: the fast 3-fixture core
  (array/stack/tree).
- `test_catalog_sweep_zero_quality_warnings`: the full canonical catalog
  (every REFERENCE_SOLUTIONS algorithm, i.e. the spec A4 "all 103 canonical
  examples[0]" corpus) with canonical example inputs executed in-process.
  Both stay under the 60s budget (local execution, capped traces).
"""

import io
import json
import sys
import time

import pytest

from app.ports.code_executor import ExecutionResult
from app.services.animation_validator import AnimationValidator
from app.services.question_catalog import QUESTION_ALGORITHMS
from app.services.reference_solutions import REFERENCE_SOLUTIONS, resolve_algorithm
from app.services.solution_animation_service import SolutionAnimationService


def test_lint_quality_flags_missing_camera_and_badge():
    v = AnimationValidator()
    script = {
        "steps": [
            {
                "narration": "Intro",
                "shapes": [],
                "motion": [{"target": "a", "op": "scale", "to": 1.0, "duration": 0.25}],
            },
            {
                "narration": "Intro",
                "shapes": [],
                "motion": [{"target": "a", "op": "scale", "to": 1.0, "duration": 0.25}],
            },
        ]
    }
    warnings = v.lint_quality(script)
    assert any("camera" in w for w in warnings)
    assert any("badge" in w for w in warnings)
    assert any("duplicate" in w for w in warnings)


class FakeExecutor:
    def __init__(self, result: ExecutionResult):
        self.result = result

    async def execute(self, language, code, stdin="", version=None):
        return self.result


def _ok(stdout: str) -> ExecutionResult:
    return ExecutionResult(stdout=stdout, stderr="", exit_code=0)


def _trace(events):
    return "\n".join(json.dumps(e) for e in events)


# Curated corpus subset: one canonical examples[0]-style fixture per family.
# Questions resolve via catalog match_keys; traces mirror the instrumented
# reference solutions (init + events + return).
FIXTURES = [
    {
        "family": "array",
        "question": {
            "id": "bubble-sort",
            "title": "Bubble Sort",
            "category": "sorting",
            "description": "Sort the array using bubble sort.",
            "examples": [{"input": "[5,1,4,2,8]", "output": "[1,2,4,5,8]"}],
        },
        "stdout": _trace(
            [
                {"event": "init", "values": [5, 1, 4, 2, 8], "family": "array"},
                {"event": "pointer", "name": "j", "index": 0},
                {"event": "compare", "i": 0, "j": 1},
                {"event": "swap", "i": 0, "j": 1},
                {"event": "pointer", "name": "j", "index": 1},
                {"event": "compare", "i": 1, "j": 2},
                {"event": "swap", "i": 1, "j": 2},
                {"event": "mark", "i": 4, "state": "sorted"},
                {"event": "return", "result": [1, 2, 4, 5, 8]},
            ]
        ),
    },
    {
        "family": "stack",
        "question": {
            "id": "valid-parentheses",
            "title": "Valid Parentheses",
            "category": "stack",
            "description": "Check whether the bracket string has valid parentheses ordering.",
            "examples": [{"input": '"()[]{}"', "output": "true"}],
        },
        "stdout": _trace(
            [
                {
                    "event": "init",
                    "values": ["(", ")", "[", "]", "{", "}"],
                    "family": "stack",
                },
                {"event": "visit", "i": 0},
                {"event": "push", "value": "("},
                {"event": "visit", "i": 1},
                {"event": "pop", "value": "("},
                {"event": "visit", "i": 2},
                {"event": "push", "value": "["},
                {"event": "visit", "i": 3},
                {"event": "pop", "value": "["},
                {"event": "visit", "i": 4},
                {"event": "push", "value": "{"},
                {"event": "visit", "i": 5},
                {"event": "pop", "value": "{"},
                {"event": "return", "result": True},
            ]
        ),
    },
    {
        "family": "tree",
        "question": {
            "id": "maximum-depth-of-binary-tree",
            "title": "Maximum Depth of Binary Tree",
            "category": "trees",
            "description": "Compute the maximum depth of binary tree.",
            "examples": [{"input": '"[3,9,20,null,null,15,7]"', "output": "3"}],
        },
        "stdout": _trace(
            [
                {
                    "event": "init",
                    "values": [3, 9, 20, None, None, 15, 7],
                    "family": "tree",
                },
                {"event": "visit", "i": 0},
                {"event": "visit", "i": 1},
                {"event": "visit", "i": 2},
                {"event": "mark", "i": 2, "state": "active"},
                {"event": "visit", "i": 5},
                {"event": "visit", "i": 6},
                {"event": "return", "result": 3},
            ]
        ),
    },
]


@pytest.mark.asyncio
async def test_corpus_gate_zero_quality_warnings():
    started = time.monotonic()
    validator = AnimationValidator()
    for fixture in FIXTURES:
        service = SolutionAnimationService(
            executor=FakeExecutor(_ok(fixture["stdout"]))
        )
        animation = await service.build_animation(fixture["question"])
        assert animation is not None, f"no animation for {fixture['family']}"
        warnings = validator.lint_quality(animation)
        assert warnings == [], f"{fixture['family']} warnings: {warnings}"
    assert time.monotonic() - started < 60


class LocalExecutor:
    """Execute the wrapped traced solution in-process: no Piston, no network."""

    async def execute(self, language, code, stdin="", version=None):
        old_stdin, old_stdout = sys.stdin, sys.stdout
        buf = io.StringIO()
        try:
            sys.stdin = io.StringIO(stdin)
            sys.stdout = buf
            exec(compile(code, "<wrapped>", "exec"), {})  # noqa: S102
        except Exception as exc:  # noqa: BLE001 - trace failure degrades to None
            return ExecutionResult(stdout="", stderr=str(exc)[:200], exit_code=1)
        finally:
            sys.stdin, sys.stdout = old_stdin, old_stdout
        return ExecutionResult(stdout=buf.getvalue(), stderr="", exit_code=0)


# Canonical example inputs mirroring each algorithm's LeetCode examples[0]
# shape (dict form, which parse_input_kwargs passes through). Three algos have
# no question-catalog id and resolve via match_keys instead.
_CATALOG_QID: dict = {}
for _qid, _algo in QUESTION_ALGORITHMS.items():
    _CATALOG_QID.setdefault(_algo, _qid)

_TREE = [3, 9, 20, None, None, 15, 7]

CATALOG_INPUTS = {
    "bubble_sort": {"values": [5, 1, 4, 2, 8]},
    "linear_search": {"values": [5, 1, 4, 2, 8], "target": 1},
    "binary_search": {"nums": [1, 3, 5, 7, 9], "target": 7},
    "two_sum": {"nums": [2, 7, 11, 15], "target": 9},
    "contains_duplicate": {"nums": [1, 2, 3, 1]},
    "majority_element": {"nums": [3, 2, 3]},
    "single_number": {"nums": [2, 2, 1]},
    "missing_number": {"nums": [3, 0, 1]},
    "find_the_duplicate_number": {"nums": [1, 3, 4, 2, 2]},
    "find_all_duplicates": {"nums": [4, 3, 2, 7, 8, 2, 3, 1]},
    "first_missing_positive": {"nums": [3, 4, -1, 1]},
    "longest_consecutive_sequence": {"nums": [100, 4, 200, 1, 3, 2]},
    "valid_anagram": {"s": "anagram", "t": "nagaram"},
    "group_anagrams": {"strs": ["eat", "tea", "tan", "ate", "nat", "bat"]},
    "top_k_frequent": {"nums": [1, 1, 1, 2, 2, 3], "k": 2},
    "product_of_array_except_self": {"nums": [1, 2, 3, 4]},
    "subarray_sum_equals_k": {"nums": [1, 1, 1], "k": 2},
    "contiguous_array": {"nums": [0, 1, 0]},
    "next_permutation": {"nums": [1, 2, 3]},
    "reverse_string": {"s": ["h", "e", "l", "l", "o"]},
    "move_zeroes": {"nums": [0, 1, 0, 3, 12]},
    "valid_palindrome": {"s": "racecar"},
    "is_subsequence": {"s": "abc", "t": "ahbgdc"},
    "two_sum_ii": {"numbers": [2, 7, 11, 15], "target": 9},
    "three_sum": {"nums": [-1, 0, 1, 2, -1, -4]},
    "three_sum_closest": {"nums": [-1, 2, 1, -4], "target": 1},
    "container_with_most_water": {"height": [1, 8, 6, 2, 5, 4, 8, 3, 7]},
    "trapping_rain_water": {"height": [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]},
    "partition_labels": {"s": "ababcbacadefegdehijhklij"},
    "longest_substring_without_repeating": {"s": "abcabcbb"},
    "permutation_in_string": {"s1": "ab", "s2": "eidbaooo"},
    "longest_repeating_character_replacement": {"s": "AABABBA", "k": 1},
    "minimum_window_substring": {"s": "ADOBECODEBANC", "t": "ABC"},
    "sliding_window_maximum": {"nums": [1, 3, -1, -3, 5, 3, 6, 7], "k": 3},
    "best_time_to_buy_and_sell": {"prices": [7, 1, 5, 3, 6, 4]},
    "jump_game": {"nums": [2, 3, 1, 1, 4]},
    "jump_game_ii": {"nums": [2, 3, 1, 1, 4]},
    "gas_station": {"gas": [1, 2, 3, 4, 5], "cost": [3, 4, 5, 1, 2]},
    "hand_of_straights": {"hand": [1, 2, 3, 6, 2, 3, 4, 7, 8], "groupSize": 3},
    "car_fleet": {
        "target": 12,
        "position": [10, 8, 0, 5, 3],
        "speed": [2, 4, 1, 1, 3],
    },
    "longest_common_prefix": {"strs": ["flower", "flow", "flight"]},
    "ransom_note": {"ransomNote": "aa", "magazine": "aab"},
    "first_word": {"s": "hello world"},
    "most_frequent_char": {"s": "abracadabra"},
    "happy_number": {"n": 19},
    "reverse_integer": {"x": 123},
    "number_of_1_bits": {"n": 11},
    "power_of_two": {"n": 16},
    "kth_largest": {"nums": [3, 2, 1, 5, 6, 4], "k": 2},
    "k_closest": {"points": [[1, 3], [-2, 2]], "k": 1},
    "task_scheduler": {"tasks": ["A", "A", "A", "B", "B", "B"], "n": 2},
    "word_ladder": {
        "beginWord": "hit",
        "endWord": "cog",
        "wordList": ["hot", "dot", "dog", "lot", "log", "cog"],
    },
    "generate_parentheses": {"n": 3},
    "permutations": {"nums": [1, 2, 3]},
    "subsets": {"nums": [1, 2]},
    "combination_sum": {"candidates": [2, 3, 6, 7], "target": 7},
    "max_subarray": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]},
    "maximum_product_subarray": {"nums": [2, 3, -2, 4]},
    "climbing_stairs": {"n": 5},
    "house_robber": {"nums": [1, 2, 3, 1]},
    "decode_ways": {"s": "226"},
    "longest_increasing_subsequence": {"nums": [10, 9, 2, 5, 3, 7, 101, 18]},
    "word_break": {"s": "leetcode", "wordDict": ["leet", "code"]},
    "coin_change": {"coins": [1, 2, 5], "amount": 11},
    "burst_balloons": {"nums": [3, 1, 5, 8]},
    "edit_distance": {"word1": "horse", "word2": "ros"},
    "valid_parentheses": {"s": "()[]{}"},
    "evaluate_reverse_polish_notation": {"tokens": ["2", "1", "+", "3", "*"]},
    "daily_temperatures": {"temperatures": [73, 74, 75, 71, 69, 72, 76, 73]},
    "largest_rectangle_in_histogram": {"heights": [2, 1, 5, 6, 2, 3]},
    "longest_valid_parentheses": {"s": ")()())"},
    "min_stack": {
        "operations": ["push", "push", "push", "getMin", "pop", "top", "getMin"],
        "values": [[-2], [0], [-3], [], [], [], []],
    },
    "reverse_linked_list": {"head": [1, 2, 3]},
    "linked_list_cycle": {"head": [3, 2, 0, -4], "pos": 1},
    "merge_two_sorted_lists": {"list1": [1, 2, 4], "list2": [1, 3, 4]},
    "add_two_numbers": {"l1": [2, 4, 3], "l2": [5, 6, 4]},
    "merge_k_sorted_lists": {"lists": [[1, 4, 5], [1, 3, 4], [2, 6]]},
    "remove_nth_node_from_end": {"head": [1, 2, 3, 4, 5], "n": 2},
    "reorder_list": {"head": [1, 2, 3, 4]},
    "maximum_depth_of_binary_tree": {"root": _TREE},
    "balanced_binary_tree": {"root": _TREE},
    "invert_binary_tree": {"root": _TREE},
    "same_tree": {"p": [1, 2, 3], "q": [1, 2, 3]},
    "validate_binary_search_tree": {"root": [2, 1, 3]},
    "binary_tree_level_order_traversal": {"root": _TREE},
    "kth_smallest_element_in_a_bst": {"root": [3, 1, 4, None, 2], "k": 1},
    "lowest_common_ancestor": {
        "root": [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5],
        "p": 2,
        "q": 8,
    },
    "binary_tree_maximum_path_sum": {"root": [-10, 9, 20, None, None, 15, 7]},
    "rotate_image": {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]},
    "number_of_islands": {"grid": [["1", "1", "0"], ["1", "0", "0"], ["0", "0", "1"]]},
    "word_search": {
        "board": [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]],
        "word": "ABCCED",
    },
    "clone_graph": {"adj": [[2, 3], [1], [1]]},
    "course_schedule": {"numCourses": 2, "prerequisites": [[1, 0]]},
    "course_schedule_ii": {"numCourses": 2, "prerequisites": [[1, 0]]},
    "search_insert_position": {"nums": [1, 3, 5, 6], "target": 5},
    "find_first_and_last": {"nums": [5, 7, 7, 8, 8, 10], "target": 8},
    "find_minimum_in_rotated": {"nums": [3, 4, 5, 1, 2]},
    "search_in_rotated": {"nums": [4, 5, 6, 7, 0, 1, 2], "target": 0},
    "koko_eating_bananas": {"piles": [3, 6, 7, 11], "h": 8},
    "median_of_two_sorted_arrays": {"nums1": [1, 3], "nums2": [2]},
    "merge_intervals": {"intervals": [[1, 3], [2, 6], [8, 10], [15, 18]]},
    "non_overlapping_intervals": {"intervals": [[1, 2], [2, 3], [3, 4], [1, 3]]},
}


def _catalog_question(algo: str) -> dict:
    """Build a question dict that resolves to `algo` exactly like the app."""
    entry = REFERENCE_SOLUTIONS[algo]
    qid = _CATALOG_QID.get(algo)
    if qid is not None:
        question = {
            "id": qid,
            "title": entry.get("title", algo),
            "category": "",
            "description": entry.get("title", algo),
        }
    else:
        question = {
            "id": f"sweep-{algo}",
            "title": entry.get("title", algo),
            "category": "",
            "description": " ".join(entry["match_keys"]),
        }
    assert resolve_algorithm(question) == algo, f"resolve failed for {algo}"
    question["examples"] = [{"input": CATALOG_INPUTS[algo], "output": ""}]
    return question


@pytest.mark.asyncio
async def test_catalog_sweep_zero_quality_warnings():
    """Full-catalog gate: every canonical algorithm animates with zero
    lint_quality warnings (spec A4). LocalExecutor runs the traced optimal
    solution in-process — no Piston, no network."""
    assert set(CATALOG_INPUTS) == set(REFERENCE_SOLUTIONS), "sweep must cover all"
    started = time.monotonic()
    validator = AnimationValidator()
    failures: list = []
    warned: dict = {}
    for algo in sorted(REFERENCE_SOLUTIONS):
        service = SolutionAnimationService(executor=LocalExecutor())
        try:
            animation = await service.build_animation(_catalog_question(algo))
        except Exception as exc:  # noqa: BLE001 - report, don't abort the sweep
            failures.append((algo, f"exception: {exc}"))
            continue
        if animation is None:
            failures.append((algo, "no animation"))
            continue
        warnings = validator.lint_quality(animation)
        if warnings:
            warned[algo] = warnings
    assert not failures, f"no-animation: {failures}"
    assert not warned, f"quality warnings: {warned}"
    assert time.monotonic() - started < 60
