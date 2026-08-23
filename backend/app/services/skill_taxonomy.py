from __future__ import annotations

from typing import Dict, List, Tuple

from app.models.skill_graph_schemas import QuestionSkill, Skill, SkillStatus

# Curated, deterministic skill taxonomy. Parent/child gives hierarchy;
# prerequisite_ids define ordering that recommendations must respect.

SKILLS: List[Skill] = [
    Skill(
        slug="programming-fundamentals",
        name="Programming Fundamentals",
        description="Basic syntax, variables, control flow, functions.",
    ),
    Skill(
        slug="arrays",
        name="Arrays",
        description="Indexing, traversal, in-place mutation, subarrays.",
        prerequisite_ids=["programming-fundamentals"],
    ),
    Skill(
        slug="strings",
        name="Strings",
        description="Character manipulation, substring operations, formatting.",
        prerequisite_ids=["programming-fundamentals"],
    ),
    Skill(
        slug="hash-maps",
        name="Hash Maps",
        description="Key/value lookup, frequency counting, complement tracking.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="two-pointers",
        name="Two Pointers",
        description="Left/right index movement, in-place swapping.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="sliding-window",
        name="Sliding Window",
        description="Fixed and variable-size windows over sequences.",
        prerequisite_ids=["two-pointers", "hash-maps"],
    ),
    Skill(
        slug="stacks-queues",
        name="Stacks & Queues",
        description="LIFO/FIFO structure patterns, monotonic stacks, deques.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="heaps",
        name="Heaps & Priority Queues",
        description="Top-k selection, scheduling, streaming order statistics.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="recursion",
        name="Recursion",
        description="Base case, recursive step, call-stack reasoning.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="backtracking",
        name="Backtracking",
        description="Systematic choice exploration with undo on dead ends.",
        prerequisite_ids=["recursion"],
    ),
    Skill(
        slug="sorting",
        name="Sorting",
        description="Compare-based sorts, stability, custom comparators.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="searching",
        name="Searching",
        description="Linear and binary search, monotonic predicates.",
        prerequisite_ids=["sorting"],
    ),
    Skill(
        slug="linked-lists",
        name="Linked Lists",
        description="Node traversal, reversal, cycle detection.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="trees",
        name="Trees",
        description="Binary trees, DFS/BFS, tree traversal orders.",
        prerequisite_ids=["recursion"],
    ),
    Skill(
        slug="graphs",
        name="Graphs",
        description="Adjacency representation, BFS/DFS, connectivity.",
        prerequisite_ids=["trees"],
    ),
    Skill(
        slug="dynamic-programming",
        name="Dynamic Programming",
        description="Overlapping subproblems, memoization, tabulation.",
        prerequisite_ids=["recursion"],
    ),
    Skill(
        slug="greedy",
        name="Greedy",
        description="Locally optimal choices proven globally safe.",
        prerequisite_ids=["arrays"],
    ),
    Skill(
        slug="bit-manipulation",
        name="Bit Manipulation",
        description="XOR tricks, masks, two's-complement arithmetic.",
        prerequisite_ids=["programming-fundamentals"],
    ),
    Skill(
        slug="debugging",
        name="Debugging",
        description="Reading error output, isolating failure, reproducing bugs.",
        prerequisite_ids=["programming-fundamentals"],
    ),
    Skill(
        slug="testing",
        name="Testing",
        description="Edge cases, unit assertions, input/output validation.",
        prerequisite_ids=["programming-fundamentals"],
    ),
    Skill(
        slug="time-complexity",
        name="Time Complexity",
        description="Big-O analysis, identifying dominant operations.",
        prerequisite_ids=["programming-fundamentals"],
    ),
    Skill(
        slug="space-complexity",
        name="Space Complexity",
        description="Auxiliary memory analysis, in-place vs. extra space.",
        prerequisite_ids=["programming-fundamentals"],
    ),
]

# Question -> [(skill_slug, weight), ...]. Keys are question IDs from the
# production question bank (seeded into Supabase); these drive skill
# attribution when a user solves a question. Weights per question sum to 1.
#
# Coverage contract: every live question id MUST appear here and every key
# MUST exist in the bank - enforced by tests/unit/test_skill_taxonomy.py
# against tests/fixtures/live_question_ids.json.
_QUESTION_SKILL_WEIGHTS: Dict[str, List[Tuple[str, float]]] = {
    # --- Arrays & Hashing -------------------------------------------------
    "two-sum": [("arrays", 0.4), ("hash-maps", 0.6)],
    "contains-duplicate": [("hash-maps", 0.7), ("arrays", 0.3)],
    "group-anagrams": [("hash-maps", 0.7), ("strings", 0.3)],
    "valid-anagram": [("hash-maps", 0.6), ("strings", 0.4)],
    "ransom-note": [("hash-maps", 0.8), ("strings", 0.2)],
    "majority-element": [("hash-maps", 0.7), ("arrays", 0.3)],
    "contiguous-array": [("hash-maps", 0.8), ("arrays", 0.2)],
    "subarray-sum-equals-k": [("hash-maps", 0.8), ("arrays", 0.2)],
    "longest-consecutive-sequence": [("hash-maps", 0.7), ("arrays", 0.3)],
    "find-all-duplicates-in-an-array": [("arrays", 0.6), ("hash-maps", 0.4)],
    "first-missing-positive": [("arrays", 0.7), ("hash-maps", 0.3)],
    "product-of-array-except-self": [("arrays", 0.8), ("time-complexity", 0.2)],
    "missing-number": [("arrays", 0.6), ("bit-manipulation", 0.4)],
    "merge-intervals": [("sorting", 0.5), ("arrays", 0.5)],
    "non-overlapping-intervals": [("greedy", 0.7), ("sorting", 0.3)],
    # --- Two Pointers -----------------------------------------------------
    "reverse-string": [("strings", 0.5), ("two-pointers", 0.5)],
    "valid-palindrome": [("two-pointers", 0.7), ("strings", 0.3)],
    "two-sum-ii-input-array-is-sorted": [("two-pointers", 0.6), ("arrays", 0.4)],
    "three-sum": [("two-pointers", 0.7), ("arrays", 0.3)],
    "three-sum-closest": [("two-pointers", 0.7), ("arrays", 0.3)],
    "container-with-most-water": [("two-pointers", 0.8), ("greedy", 0.2)],
    "move-zeroes": [("two-pointers", 0.7), ("arrays", 0.3)],
    "is-subsequence": [("two-pointers", 0.8), ("strings", 0.2)],
    "partition-labels": [("two-pointers", 0.6), ("greedy", 0.4)],
    "rotate-image": [("two-pointers", 0.7), ("arrays", 0.3)],
    "trapping-rain-water": [("two-pointers", 0.7), ("stacks-queues", 0.3)],
    # --- Sliding Window ---------------------------------------------------
    "best-time-to-buy-and-sell-stock": [("sliding-window", 0.6), ("arrays", 0.4)],
    "longest-substring-without-repeating-characters": [
        ("sliding-window", 0.8),
        ("strings", 0.2),
    ],
    "longest-repeating-character-replacement": [
        ("sliding-window", 0.9),
        ("hash-maps", 0.1),
    ],
    "minimum-window-substring": [("sliding-window", 0.7), ("hash-maps", 0.3)],
    "permutation-in-string": [("sliding-window", 0.7), ("hash-maps", 0.3)],
    "sliding-window-maximum": [("sliding-window", 0.6), ("stacks-queues", 0.4)],
    # --- Stacks & Queues --------------------------------------------------
    "valid-parentheses": [("stacks-queues", 0.8), ("time-complexity", 0.2)],
    "evaluate-reverse-polish-notation": [
        ("stacks-queues", 0.9),
        ("programming-fundamentals", 0.1),
    ],
    "min-stack": [("stacks-queues", 0.8), ("arrays", 0.2)],
    "daily-temperatures": [("stacks-queues", 0.8), ("arrays", 0.2)],
    "car-fleet": [("stacks-queues", 0.6), ("sorting", 0.4)],
    "largest-rectangle-in-histogram": [("stacks-queues", 0.8), ("two-pointers", 0.2)],
    "longest-valid-parentheses": [("stacks-queues", 0.7), ("dynamic-programming", 0.3)],
    # --- Heaps & Priority Queues -------------------------------------------
    "top-k-frequent-elements": [("heaps", 0.7), ("hash-maps", 0.3)],
    "k-closest-points-to-origin": [("heaps", 0.7), ("sorting", 0.3)],
    "kth-largest-element-in-an-array": [("heaps", 0.7), ("sorting", 0.3)],
    "task-scheduler": [("heaps", 0.6), ("greedy", 0.4)],
    "hand-of-straights": [("heaps", 0.6), ("hash-maps", 0.4)],
    "merge-k-sorted-lists": [("heaps", 0.6), ("linked-lists", 0.4)],
    # --- Binary Search ------------------------------------------------------
    "binary-search": [("searching", 1.0)],
    "search-insert-position": [("searching", 0.8), ("arrays", 0.2)],
    "find-first-and-last-position-in-sorted-array": [
        ("searching", 0.8),
        ("arrays", 0.2),
    ],
    "find-minimum-in-rotated-sorted-array": [("searching", 0.9), ("arrays", 0.1)],
    "search-in-rotated-sorted-array": [("searching", 0.8), ("two-pointers", 0.2)],
    "koko-eating-bananas": [("searching", 0.8), ("greedy", 0.2)],
    "median-of-two-sorted-arrays": [("searching", 0.8), ("two-pointers", 0.2)],
    # --- Linked Lists -------------------------------------------------------
    "reverse-linked-list": [("linked-lists", 1.0)],
    "linked-list-cycle": [("linked-lists", 1.0)],
    "merge-two-sorted-lists": [("linked-lists", 0.8), ("two-pointers", 0.2)],
    "add-two-numbers": [("linked-lists", 0.8), ("programming-fundamentals", 0.2)],
    "remove-nth-node-from-end-of-list": [("linked-lists", 0.8), ("two-pointers", 0.2)],
    "reorder-list": [("linked-lists", 0.7), ("two-pointers", 0.3)],
    # --- Trees ---------------------------------------------------------------
    "invert-binary-tree": [("trees", 0.8), ("recursion", 0.2)],
    "maximum-depth-of-binary-tree": [("trees", 0.8), ("recursion", 0.2)],
    "same-tree": [("trees", 0.8), ("recursion", 0.2)],
    "balanced-binary-tree": [("trees", 0.8), ("recursion", 0.2)],
    "binary-tree-level-order-traversal": [("trees", 0.8), ("graphs", 0.2)],
    "validate-binary-search-tree": [("trees", 0.8), ("recursion", 0.2)],
    "kth-smallest-element-in-a-bst": [("trees", 0.8), ("searching", 0.2)],
    "lowest-common-ancestor-of-a-binary-tree": [("trees", 0.8), ("recursion", 0.2)],
    "binary-tree-maximum-path-sum": [("trees", 0.8), ("dynamic-programming", 0.2)],
    # --- Graphs ----------------------------------------------------------------
    "number-of-islands": [("graphs", 1.0)],
    "clone-graph": [("graphs", 0.8), ("hash-maps", 0.2)],
    "course-schedule": [("graphs", 0.8), ("recursion", 0.2)],
    "course-schedule-ii": [("graphs", 0.8), ("sorting", 0.2)],
    "word-ladder": [("graphs", 0.7), ("searching", 0.3)],
    "word-search": [("backtracking", 0.8), ("graphs", 0.2)],
    "e42b2609-8b2c-49a0-9fa3-b7145df07bc3": [("graphs", 0.6), ("heaps", 0.4)],
    # --- Dynamic Programming -----------------------------------------------------
    "climbing-stairs": [("dynamic-programming", 0.8), ("recursion", 0.2)],
    "coin-change": [("dynamic-programming", 1.0)],
    "house-robber": [("dynamic-programming", 1.0)],
    "word-break": [("dynamic-programming", 0.8), ("strings", 0.2)],
    "edit-distance": [("dynamic-programming", 0.8), ("strings", 0.2)],
    "decode-ways": [("dynamic-programming", 0.8), ("strings", 0.2)],
    "longest-increasing-subsequence": [("dynamic-programming", 0.9), ("arrays", 0.1)],
    "burst-balloons": [("dynamic-programming", 0.9), ("arrays", 0.1)],
    "maximum-product-subarray": [("dynamic-programming", 0.7), ("arrays", 0.3)],
    # --- Backtracking --------------------------------------------------------------
    "permutations": [("backtracking", 0.9), ("recursion", 0.1)],
    "subsets": [("backtracking", 0.9), ("recursion", 0.1)],
    "combination-sum": [("backtracking", 0.8), ("recursion", 0.2)],
    "generate-parentheses": [("backtracking", 0.7), ("stacks-queues", 0.3)],
    # --- Greedy ----------------------------------------------------------------------
    "jump-game": [("greedy", 0.8), ("arrays", 0.2)],
    "jump-game-ii": [("greedy", 0.9), ("arrays", 0.1)],
    "gas-station": [("greedy", 0.8), ("arrays", 0.2)],
    "next-permutation": [("greedy", 0.7), ("two-pointers", 0.3)],
    # --- Bit Manipulation ---------------------------------------------------------
    "single-number": [("bit-manipulation", 0.9), ("arrays", 0.1)],
    "number-of-1-bits": [("bit-manipulation", 0.9), ("programming-fundamentals", 0.1)],
    "power-of-two": [("bit-manipulation", 0.8), ("programming-fundamentals", 0.2)],
    "reverse-integer": [("bit-manipulation", 0.6), ("programming-fundamentals", 0.4)],
    "find-the-duplicate-number": [("two-pointers", 0.7), ("bit-manipulation", 0.3)],
    # --- Strings (bank-specific themed questions) ------------------------------------
    "happy-number": [("two-pointers", 0.6), ("hash-maps", 0.4)],
    "longest-common-prefix": [("strings", 0.8), ("arrays", 0.2)],
    "c9d1a3f2-5b6e-4a7f-8c0d-1e2f3a4b5c6d": [
        ("strings", 0.8),
        ("programming-fundamentals", 0.2),
    ],
    "7b9d2c1a-3e4f-5a6b-7c8d-9e0f1a2b3c4d": [("hash-maps", 0.8), ("strings", 0.2)],
    "5d8c4a1f-2b3e-4f6a-8c9d-0e1f2a3b4c5d": [
        ("strings", 0.7),
        ("programming-fundamentals", 0.3),
    ],
    "2b6e5f1a-4c7d-4a8e-9b0c-1d2e3f4a5b6c": [
        ("strings", 0.8),
        ("programming-fundamentals", 0.2),
    ],
    "6d7e8f9a-0b1c-4d2e-3f4a-5b6c7d8e9f0a": [("strings", 0.7), ("two-pointers", 0.3)],
    "1f3e5d7c-9b8a-4c6d-0e2f-4a5b6c7d8e9f": [
        ("dynamic-programming", 0.8),
        ("strings", 0.2),
    ],
    "8c3d2e4f-6a5b-4f7c-9d0e-1a2b3c4d5e6f": [
        ("dynamic-programming", 0.8),
        ("strings", 0.2),
    ],
    "9e4f5a6b-7c8d-4e9f-0a1b-2c3d4e5f6a7b": [
        ("dynamic-programming", 0.8),
        ("strings", 0.2),
    ],
    "4a3f7c1e-5d6b-4e8f-9a0c-2b3d4e5f6a7b": [
        ("dynamic-programming", 0.7),
        ("strings", 0.3),
    ],
}


def _build_question_skills() -> Dict[str, List[QuestionSkill]]:
    return {
        question_id: [
            QuestionSkill(question_id=question_id, skill_slug=slug, weight=weight)
            for slug, weight in mappings
        ]
        for question_id, mappings in _QUESTION_SKILL_WEIGHTS.items()
    }


QUESTION_SKILLS: Dict[str, List[QuestionSkill]] = _build_question_skills()

# Deterministic evidence constants used by the rules engine. These are tuned
# initial values; calibration happens in simulation, never via ML.
EVIDENCE = {
    "submission_passed_independent": 1.0,
    "submission_passed_after_hint": 0.5,
    "submission_passed_after_solution": 0.2,
    "submission_failed": -0.3,
    "repeated_error": -0.5,
    "hint_requested": -0.1,
    "lesson_completed": 0.15,
    "review_passed": 0.4,
    "review_failed": -0.2,
    "diagnosis_created": 0.0,
}

# Mastery thresholds for status derivation.
STATUS_THRESHOLDS: List[Tuple[float, SkillStatus]] = [
    (0.75, SkillStatus.STRONG),
    (0.45, SkillStatus.DEVELOPING),
    (0.2, SkillStatus.LEARNING),
    (float("-inf"), SkillStatus.NEW),
]

# Confidence grows with evidence, saturating at CONFIDENCE_CAP.
CONFIDENCE_PER_EVENT = 0.15
CONFIDENCE_CAP = 0.9

# Breadth cap: mastery from a single question is bounded so memorizing one
# problem cannot mark a skill as mastered. Each distinct question raises the
# ceiling; the cap equals DISTINCT_QUESTION_CEILING per distinct question.
DISTINCT_QUESTION_CEILING = 0.3

# Time-based decay: mastery drops after MAX_INACTIVE_DAYS of no practice.
DECAY_ENABLED = True
MAX_INACTIVE_DAYS = 7.0
DECAY_PER_DAY = 0.02
# Knowledge never decays all the way to zero — prior experience keeps a floor.
DECAY_FLOOR = 0.05

# Bounds to keep a single event from swinging state dramatically.
# Positive evidence scales against the independent-pass reference (1.0) so an
# independent solve earns the full cap while hinted/solution passes earn less.
MAX_MASTERY_DELTA_PER_EVENT = 0.3
POSITIVE_REFERENCE = 1.0
# Failures reduce mastery multiplicatively: a single slip costs 12% of current
# mastery, a repeated error costs 24% — a strong skill survives one slip.
FAIL_REDUCTION = 0.12
REPEATED_FAIL_REDUCTION = 0.24
REVIEW_FAIL_REDUCTION = 0.1
HINT_PENALTY = 0.02
MIN_MASTERY = 0.0
MAX_MASTERY = 1.0
