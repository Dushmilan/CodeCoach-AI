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
        slug="recursion",
        name="Recursion",
        description="Base case, recursive step, call-stack reasoning.",
        prerequisite_ids=["arrays"],
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

# Question -> skills mapping with weights. Keys are question IDs from the
# production question bank (seeded into Supabase); these drive skill
# attribution when a user solves a question.
QUESTION_SKILLS: Dict[str, List[QuestionSkill]] = {
    "two-sum": [
        QuestionSkill(question_id="two-sum", skill_slug="arrays", weight=0.4),
        QuestionSkill(question_id="two-sum", skill_slug="hash-maps", weight=0.6),
    ],
    "contains-duplicate": [
        QuestionSkill(
            question_id="contains-duplicate", skill_slug="hash-maps", weight=0.7
        ),
        QuestionSkill(
            question_id="contains-duplicate", skill_slug="arrays", weight=0.3
        ),
    ],
    "group-anagrams": [
        QuestionSkill(question_id="group-anagrams", skill_slug="hash-maps", weight=0.7),
        QuestionSkill(question_id="group-anagrams", skill_slug="strings", weight=0.3),
    ],
    "valid-anagram": [
        QuestionSkill(question_id="valid-anagram", skill_slug="hash-maps", weight=0.6),
        QuestionSkill(question_id="valid-anagram", skill_slug="strings", weight=0.4),
    ],
    "reverse-string": [
        QuestionSkill(question_id="reverse-string", skill_slug="strings", weight=0.5),
        QuestionSkill(
            question_id="reverse-string", skill_slug="two-pointers", weight=0.5
        ),
    ],
    "valid-palindrome": [
        QuestionSkill(
            question_id="valid-palindrome", skill_slug="two-pointers", weight=0.7
        ),
        QuestionSkill(question_id="valid-palindrome", skill_slug="strings", weight=0.3),
    ],
    "two-sum-ii-input-array-is-sorted": [
        QuestionSkill(
            question_id="two-sum-ii-input-array-is-sorted",
            skill_slug="two-pointers",
            weight=0.6,
        ),
        QuestionSkill(
            question_id="two-sum-ii-input-array-is-sorted",
            skill_slug="arrays",
            weight=0.4,
        ),
    ],
    "best-time-to-buy-and-sell-stock": [
        QuestionSkill(
            question_id="best-time-to-buy-and-sell-stock",
            skill_slug="sliding-window",
            weight=0.6,
        ),
        QuestionSkill(
            question_id="best-time-to-buy-and-sell-stock",
            skill_slug="arrays",
            weight=0.4,
        ),
    ],
    "longest-substring-without-repeating-characters": [
        QuestionSkill(
            question_id="longest-substring-without-repeating-characters",
            skill_slug="sliding-window",
            weight=0.8,
        ),
        QuestionSkill(
            question_id="longest-substring-without-repeating-characters",
            skill_slug="strings",
            weight=0.2,
        ),
    ],
    "climbing-stairs": [
        QuestionSkill(
            question_id="climbing-stairs", skill_slug="dynamic-programming", weight=0.8
        ),
        QuestionSkill(
            question_id="climbing-stairs", skill_slug="recursion", weight=0.2
        ),
    ],
    "coin-change": [
        QuestionSkill(
            question_id="coin-change", skill_slug="dynamic-programming", weight=0.9
        ),
    ],
    "house-robber": [
        QuestionSkill(
            question_id="house-robber", skill_slug="dynamic-programming", weight=0.9
        ),
    ],
    "merge-intervals": [
        QuestionSkill(question_id="merge-intervals", skill_slug="sorting", weight=0.5),
        QuestionSkill(question_id="merge-intervals", skill_slug="arrays", weight=0.5),
    ],
    "binary-search": [
        QuestionSkill(question_id="binary-search", skill_slug="searching", weight=0.9),
    ],
    "search-insert-position": [
        QuestionSkill(
            question_id="search-insert-position", skill_slug="searching", weight=0.8
        ),
        QuestionSkill(
            question_id="search-insert-position", skill_slug="arrays", weight=0.2
        ),
    ],
    "reverse-linked-list": [
        QuestionSkill(
            question_id="reverse-linked-list", skill_slug="linked-lists", weight=0.9
        ),
    ],
    "linked-list-cycle": [
        QuestionSkill(
            question_id="linked-list-cycle", skill_slug="linked-lists", weight=0.9
        ),
    ],
    "invert-binary-tree": [
        QuestionSkill(question_id="invert-binary-tree", skill_slug="trees", weight=0.8),
        QuestionSkill(
            question_id="invert-binary-tree", skill_slug="recursion", weight=0.2
        ),
    ],
    "maximum-depth-of-binary-tree": [
        QuestionSkill(
            question_id="maximum-depth-of-binary-tree", skill_slug="trees", weight=0.8
        ),
        QuestionSkill(
            question_id="maximum-depth-of-binary-tree",
            skill_slug="recursion",
            weight=0.2,
        ),
    ],
    "number-of-islands": [
        QuestionSkill(question_id="number-of-islands", skill_slug="graphs", weight=0.9),
    ],
    "valid-parentheses": [
        QuestionSkill(question_id="valid-parentheses", skill_slug="arrays", weight=0.2),
        QuestionSkill(
            question_id="valid-parentheses", skill_slug="debugging", weight=0.3
        ),
        QuestionSkill(
            question_id="valid-parentheses", skill_slug="time-complexity", weight=0.2
        ),
        QuestionSkill(
            question_id="valid-parentheses", skill_slug="testing", weight=0.3
        ),
    ],
    "test-two-sum": [
        QuestionSkill(question_id="test-two-sum", skill_slug="arrays", weight=0.4),
        QuestionSkill(question_id="test-two-sum", skill_slug="hash-maps", weight=0.6),
    ],
    "test-reverse-string": [
        QuestionSkill(
            question_id="test-reverse-string", skill_slug="strings", weight=0.5
        ),
        QuestionSkill(
            question_id="test-reverse-string", skill_slug="two-pointers", weight=0.5
        ),
    ],
    "test-max-subarray": [
        QuestionSkill(
            question_id="test-max-subarray",
            skill_slug="dynamic-programming",
            weight=0.7,
        ),
        QuestionSkill(question_id="test-max-subarray", skill_slug="arrays", weight=0.3),
    ],
    "test-merge-intervals": [
        QuestionSkill(
            question_id="test-merge-intervals", skill_slug="arrays", weight=0.6
        ),
        QuestionSkill(
            question_id="test-merge-intervals", skill_slug="sorting", weight=0.4
        ),
    ],
}

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
