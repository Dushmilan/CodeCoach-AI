"""
Test configuration and fixtures for CodeCoach AI API testing.
"""

import asyncio
import os
import urllib.parse

# Set safe defaults BEFORE app.main is imported so that Settings() does not
# fail-fast at collection time (ENVIRONMENT unset = production = requires a
# JWT secret). Individual tests override via monkeypatch/test_env_vars.
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!!")

_TEST_DB = "codecoach_test"

# Under pytest-xdist each worker process imports this module and resets the
# schema; give every worker its own schema so parallel runs never race on the
# same `codecoach_test` object (e.g. gw0 -> codecoach_test_gw0).
_xdist_worker = os.environ.get("PYTEST_XDIST_WORKER")
if _xdist_worker:
    _TEST_DB = f"{_TEST_DB}_{_xdist_worker}"


def _strip_pgbouncer(url: str) -> str:
    """Drop the Supabase transaction-pooler `?pgbouncer=true` param.

    asyncpg / SQLAlchemy would otherwise forward `pgbouncer` as an unknown
    connection kwarg. Schema tooling talks to the session pooler directly, so
    the param is meaningless here.
    """
    if "pgbouncer" not in url:
        return url
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    params = [
        kv
        for kv in (query.split("&") if query else [])
        if not kv.startswith("pgbouncer")
    ]
    return urllib.parse.urlunsplit((scheme, netloc, path, "&".join(params), fragment))


def _ensure_test_database() -> str:
    """Route tests to a dedicated `codecoach_test` schema.

    Supabase exposes a single database, so isolation is a `codecoach_test`
    schema on the same server (set via `DATABASE_SEARCH_PATH`).

    Runs at import time so Settings() picks it up before app.main is loaded.
    """
    from dotenv import load_dotenv, find_dotenv

    from tests.db_guard import assert_test_db_allowed

    load_dotenv(find_dotenv())

    base_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://codecoach:codecoach@127.0.0.1:5432/codecoach",
    )
    # Never run the suite against the production pooler unless explicitly
    # overridden — the suite drops/recreates an isolated schema and runs DDL.
    assert_test_db_allowed(
        base_url,
        allow_production=os.environ.get("ALLOW_PRODUCTION_TEST_DB"),
    )
    return _ensure_postgres_test_schema(base_url)


def _ensure_postgres_test_schema(base_url: str) -> str:
    """Point DATABASE_URL at a dedicated `codecoach_test` schema.

    The ORM metadata is recreated on that schema, and `search_path` is set via
    the connection so every app query targets it.
    """
    import asyncpg

    base_url = _strip_pgbouncer(base_url)

    async def _setup() -> None:
        conn = await asyncpg.connect(base_url)
        try:
            await conn.execute(f'DROP SCHEMA IF EXISTS "{_TEST_DB}" CASCADE')
            await conn.execute(f'CREATE SCHEMA "{_TEST_DB}"')
        finally:
            await conn.close()

    asyncio.run(_setup())

    os.environ["DATABASE_URL"] = base_url
    os.environ["DATABASE_SEARCH_PATH"] = _TEST_DB

    # Rebuild from a clean slate so leftover migration-only tables never
    # conflict, retrying transient network/DDL errors.
    import time as _time

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base

    async def _create_schema_async() -> None:
        engine = create_async_engine(
            base_url.replace("postgresql://", "postgresql+asyncpg://", 1),
            poolclass=NullPool,
            connect_args={
                "server_settings": {"search_path": _TEST_DB},
                # Supabase poolers reuse prepared-statement names across
                # connections; disable asyncpg's statement cache so
                # `create_all` does not hit DuplicatePreparedStatementError.
                "statement_cache_size": 0,
            },
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    for _attempt in range(1, 6):
        try:
            asyncio.run(_create_schema_async())
            break
        except Exception:  # noqa: BLE001 - transient DDL/network race is broad
            if _attempt == 5:
                raise
            _time.sleep(0.5 * _attempt)
    return base_url


_ensure_test_database()

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from typing import Generator, AsyncGenerator  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402

from app.main import app  # noqa: E402
from app.services.question_bank import QuestionBank  # noqa: E402


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Create a test client for synchronous testing."""
    with TestClient(app) as client:
        yield client


def _test_engine_kwargs() -> dict:
    """Shared engine kwargs: force asyncpg driver + test search_path."""
    db_url = os.environ["DATABASE_URL"]
    if db_url.startswith("postgresql://"):
        return {
            "connect_args": {
                "server_settings": {"search_path": os.environ["DATABASE_SEARCH_PATH"]},
                # Supabase poolers reuse prepared-statement names across
                # connections; disable asyncpg's statement cache so DDL / DML does
                # not hit DuplicatePreparedStatementError.
                "statement_cache_size": 0,
            }
        }
    return {}


def _test_db_url() -> str:
    """Return the test DATABASE_URL with the asyncpg driver forced."""
    db_url = _strip_pgbouncer(os.environ["DATABASE_URL"])
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return db_url


_TEST_QUESTIONS = [
    {
        "id": "contains-duplicate",
        "title": "Contains Duplicate",
        "difficulty": "easy",
        "category": "arrays",
        "company_tags": ["Amazon"],
        "description": (
            "Given an integer array nums, return true if any value appears "
            "at least twice in the array."
        ),
        "starter": {
            "python": "def contains_duplicate(nums):\n    pass",
            "javascript": "function containsDuplicate(nums) {}",
            "java": "class Solution { public boolean containsDuplicate(int[] nums) { return false; } }",
        },
        "examples": [{"input": "[1,2,3,1]", "output": "true"}],
        "test_cases": [
            {"input": "[1,2,3,1]", "expected_output": "true", "hidden": False},
            {"input": "[1,2,3,4]", "expected_output": "false", "hidden": False},
        ],
        "hints": ["Compare the set size to the array length."],
        "solution": (
            "def contains_duplicate(nums):\n    return len(set(nums)) != len(nums)"
        ),
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "constraints": ["1 <= nums.length <= 10^5"],
        "is_interactive": False,
    },
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "category": "arrays",
        "company_tags": ["Google"],
        "description": (
            "Given an array of integers nums and an integer target, return the "
            "indices of the two numbers that add up to the target."
        ),
        "starter": {
            "python": "def two_sum(nums, target):\n    pass",
            "javascript": "function twoSum(nums, target) {}",
            "java": "class Solution { public int[] twoSum(int[] nums, int target) { return null; } }",
        },
        "examples": [
            {
                "input": "[2,7,11,15], 9",
                "output": "[0,1]",
                "explanation": "Basic case",
            }
        ],
        "test_cases": [
            {
                "input": "[2,7,11,15]\n9",
                "expected_output": "[0,1]",
                "hidden": False,
            }
        ],
        "hints": ["Use a hash map."],
        "solution": (
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        diff = target - n\n"
            "        if diff in seen:\n"
            "            return [seen[diff], i]\n"
            "        seen[n] = i\n"
            "    return []"
        ),
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "constraints": ["2 <= nums.length <= 10^4"],
        "is_interactive": False,
    },
    {
        "id": "reverse-string",
        "title": "Reverse String",
        "difficulty": "easy",
        "category": "strings",
        "company_tags": ["Meta"],
        "description": "Reverse the characters of a string in place.",
        "starter": {
            "python": "def reverse_string(s):\n    pass",
            "javascript": "function reverseString(s) {}",
            "java": "class Solution { public void reverseString(char[] s) {} }",
        },
        "examples": [
            {
                "input": '["h","e","l","l","o"]',
                "output": '["o","l","l","e","h"]',
                "explanation": "Reversed",
            }
        ],
        "test_cases": [
            {
                "input": '["h","e","l","l","o"]',
                "expected_output": '["o","l","l","e","h"]',
                "hidden": False,
            }
        ],
        "hints": ["Use two pointers."],
        "solution": "Swap the first and last characters, moving inward.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "constraints": ["1 <= s.length <= 10^5"],
        "is_interactive": False,
    },
    {
        "id": "maximum-product-subarray",
        "title": "Maximum Subarray",
        "difficulty": "medium",
        "category": "dynamic-programming",
        "company_tags": ["Amazon"],
        "description": "Find the contiguous subarray with the largest sum.",
        "starter": {
            "python": "def max_sub_array(nums):\n    pass",
            "javascript": "function maxSubArray(nums) {}",
            "java": "class Solution { public int maxSubArray(int[] nums) { return 0; } }",
        },
        "examples": [
            {
                "input": "[-2,1,-3,4,-1,2,1,-5,4]",
                "output": "6",
                "explanation": "Subarray [4,-1,2,1] has the largest sum.",
            }
        ],
        "test_cases": [
            {
                "input": "[-2,1,-3,4,-1,2,1,-5,4]",
                "expected_output": "6",
                "hidden": False,
            }
        ],
        "hints": ["Kadane's algorithm."],
        "solution": "Track a running sum, resetting when it drops below zero.",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "constraints": ["1 <= nums.length <= 10^5"],
        "is_interactive": False,
    },
    {
        "id": "merge-intervals",
        "title": "Merge Intervals",
        "difficulty": "hard",
        "category": "arrays",
        "company_tags": ["Microsoft"],
        "description": "Merge all overlapping intervals into one.",
        "starter": {
            "python": "def merge(intervals):\n    pass",
            "javascript": "function merge(intervals) {}",
            "java": "class Solution { public int[][] merge(int[][] intervals) { return null; } }",
        },
        "examples": [
            {
                "input": "[[1,3],[2,6],[8,10],[15,18]]",
                "output": "[[1,6],[8,10],[15,18]]",
                "explanation": "Overlapping intervals are merged.",
            }
        ],
        "test_cases": [
            {
                "input": "[[1,3],[2,6],[8,10],[15,18]]",
                "expected_output": "[[1,6],[8,10],[15,18]]",
                "hidden": False,
            }
        ],
        "hints": ["Sort by start time."],
        "solution": "Sort intervals by start, then merge overlapping ones.",
        "time_complexity": "O(n log n)",
        "space_complexity": "O(n)",
        "constraints": ["1 <= intervals.length <= 10^4"],
        "is_interactive": False,
    },
]

# Extended seed inventory: (algo_key, id, difficulty, category, description,
# example_input, example_output). Titles, starter stubs and solutions come
# straight from the reference catalog so seeds always resolve via
# resolve_algorithm; descriptions are kept keyword-clean so the longest-key
# match lands on the intended algorithm. 5 hand-written seeds above + 45 here
# = 50, the minimum the animation-coverage gate asserts on.
_EXTRA_SEED_SPECS = [
    # array (+12)
    ("best_time_to_buy_and_sell", "best-time-to-buy-and-sell-stock", "easy", "arrays",
     "Given daily prices, pick one day to buy and a later day to sell to maximize your profit.",
     "[7,1,5,3,6,4]", "5"),
    ("binary_search", "binary-search", "easy", "arrays",
     "Given a sorted array, return the index of the target using binary search, or -1.",
     "[-1,0,3,5,9,12], 9", "4"),
    ("climbing_stairs", "climbing-stairs", "easy", "arrays",
     "Count the distinct ways to reach step n taking 1 or 2 steps (climbing stairs).",
     "5", "8"),
    ("coin_change", "coin-change", "medium", "arrays",
     "Fewest coins from the given denominations that make up the amount (coin change).",
     "[1,2,5], 11", "3"),
    ("container_with_most_water", "container-with-most-water", "medium", "arrays",
     "Two lines hold water; find the container with most water.",
     "[1,8,6,2,5,4,8,3,7]", "49"),
    ("group_anagrams", "group-anagrams", "medium", "arrays",
     "Group the input strings into anagram groups (group anagrams).",
     '["eat","tea","tan","ate","nat","bat"]', '[["eat","tea","ate"],["tan","nat"],["bat"]]'),
    ("house_robber", "house-robber", "medium", "arrays",
     "Max loot without robbing adjacent houses (house robber).",
     "[1,2,3,1]", "4"),
    ("jump_game", "jump-game", "medium", "arrays",
     "Each element is a max jump length; can you reach the last index (jump game)?",
     "[2,3,1,1,4]", "true"),
    ("product_of_array_except_self", "product-of-array-except-self", "medium", "arrays",
     "For each index return the product of array except self, without division.",
     "[1,2,3,4]", "[24,12,8,6]"),
    ("three_sum", "three-sum", "medium", "arrays",
     "Find all unique triplets that sum to zero (three sum).",
     "[-1,0,1,2,-1,-4]", "[[-1,-1,2],[-1,0,1]]"),
    ("top_k_frequent", "top-k-frequent-elements", "medium", "arrays",
     "Return the k most frequent elements (top k frequent).",
     "[1,1,1,2,2,3], 2", "[1,2]"),
    ("valid_anagram", "valid-anagram", "easy", "arrays",
     "Return true if the second string is a valid anagram of the first.",
     '"anagram", "nagaram"', "true"),
    # stack (+6)
    ("daily_temperatures", "daily-temperatures", "medium", "stack",
     "For each day, how many days until a warmer temperature (daily temperatures)?",
     "[73,74,75,71,69,72,76,73]", "[1,1,4,2,1,1,0,0]"),
    ("evaluate_reverse_polish_notation", "evaluate-reverse-polish-notation", "medium", "stack",
     "Evaluate an expression in reverse polish notation.",
     '["2","1","+","3","*"]', "9"),
    ("largest_rectangle_in_histogram", "largest-rectangle-in-histogram", "hard", "stack",
     "Largest rectangle area in a histogram (largest rectangle in histogram).",
     "[2,1,5,6,2,3]", "10"),
    ("longest_valid_parentheses", "longest-valid-parentheses", "hard", "stack",
     "Length of the longest valid parentheses substring.",
     '"(()"', "2"),
    ("min_stack", "min-stack", "medium", "stack",
     "Stack supporting push, pop, top and getMin in O(1) (min stack).",
     '"push -2, push 0, push -3, getMin"', "-3"),
    ("valid_parentheses", "valid-parentheses", "easy", "stack",
     "Check whether the bracket string has valid parentheses ordering.",
     '"()[]{}"', "true"),
    # linked_list (+6)
    ("add_two_numbers", "add-two-numbers", "medium", "linked-list",
     "Add two numbers stored as reversed digit lists (add two numbers).",
     '"[2,4,3]", "[5,6,4]"', '"[7,0,8]"'),
    ("linked_list_cycle", "linked-list-cycle", "easy", "linked-list",
     "Detect whether a linked list cycle exists.",
     '"[3,2,0,-4]", pos=1', "true"),
    ("merge_k_sorted_lists", "merge-k-sorted-lists", "hard", "linked-list",
     "Merge k sorted lists into one sorted list (merge k sorted lists).",
     '"[[1,4,5],[1,3,4],[2,6]]"', '"[1,1,2,3,4,4,5,6]"'),
    ("merge_two_sorted_lists", "merge-two-sorted-lists", "easy", "linked-list",
     "Merge two sorted lists into one sorted list (merge two sorted lists).",
     '"[1,2,4]", "[1,3,4]"', '"[1,1,2,3,4,4]"'),
    ("remove_nth_node_from_end", "remove-nth-node-from-end", "medium", "linked-list",
     "Remove nth node from the end of the list (remove nth node).",
     '"[1,2,3,4,5]", 2', '"[1,2,3,5]"'),
    ("reverse_linked_list", "reverse-linked-list", "easy", "linked-list",
     "Reverse a singly linked list (reverse linked list).",
     '"[1,2,3,4,5]"', '"[5,4,3,2,1]"'),
    # tree (+7)
    ("balanced_binary_tree", "balanced-binary-tree", "easy", "trees",
     "Check whether the tree is a balanced binary tree (height-balanced).",
     '"[3,9,20,null,null,15,7]"', "true"),
    ("binary_tree_level_order_traversal", "binary-tree-level-order-traversal", "medium", "trees",
     "Return the level order traversal of the binary tree, level by level.",
     '"[3,9,20,null,null,15,7]"', '"[[3],[9,20],[15,7]]"'),
    ("invert_binary_tree", "invert-binary-tree", "easy", "trees",
     "Mirror the tree in place (invert binary tree).",
     '"[4,2,7,1,3,6,9]"', '"[4,7,2,9,6,3,1]"'),
    ("lowest_common_ancestor", "lowest-common-ancestor", "medium", "trees",
     "Find the lowest common ancestor of nodes p and q.",
     '"[3,5,1,6,2,0,8,null,null,7,4]", p=5, q=1', "3"),
    ("maximum_depth_of_binary_tree", "maximum-depth-of-binary-tree", "easy", "trees",
     "Compute the maximum depth of binary tree.",
     '"[3,9,20,null,null,15,7]"', "3"),
    ("same_tree", "same-tree", "easy", "trees",
     "Return true when two binary trees are the same tree.",
     '"[1,2,3]", "[1,2,3]"', "true"),
    ("validate_binary_search_tree", "validate-binary-search-tree", "medium", "trees",
     "Validate binary search tree ordering over the whole tree.",
     '"[2,1,3]"', "true"),
    # grid (+4; family has 3 algorithms, so one reuses number_of_islands)
    ("number_of_islands", "number-of-islands", "medium", "matrices",
     "Count the number of islands of 1s in the grid (number of islands).",
     '"[[1,1,0],[0,1,0],[1,0,1]]"', "3"),
    ("number_of_islands", "number-of-islands-archipelago", "medium", "matrices",
     "Count the archipelago: another number of islands map to tally.",
     '"[[1,0,1],[0,0,0],[1,0,1]]"', "4"),
    ("rotate_image", "rotate-image", "medium", "matrices",
     "Rotate the n x n image 90 degrees clockwise in place (rotate image).",
     '"[[1,2,3],[4,5,6],[7,8,9]]"', '"[[7,4,1],[8,5,2],[9,6,3]]"'),
    ("word_search", "word-search", "medium", "matrices",
     "Check whether the word can be traced on the board (word search).",
     '"board ABCE/SFCS/ADEE, word ABCCED"', "true"),
    # graph (+4; family has 3 algorithms, so one reuses clone_graph)
    ("clone_graph", "clone-graph", "medium", "graphs",
     "Deep-copy the connected undirected graph (clone graph).",
     '"[[2,4],[1,3],[2,4],[1,3]]"', '"[[2,4],[1,3],[2,4],[1,3]]"'),
    ("clone_graph", "clone-graph-social-network", "medium", "graphs",
     "Copy a social network adjacency snapshot (clone graph on new data).",
     '"[[2],[1]]"', '"[[2],[1]]"'),
    ("course_schedule", "course-schedule", "medium", "graphs",
     "Can all courses finish given prerequisites (course schedule)?",
     '"2 courses, [[1,0]]"', "true"),
    ("course_schedule_ii", "course-schedule-ii", "medium", "graphs",
     "Return a valid course order for course schedule ii, or empty.",
     '"2 courses, [[1,0]]"', '"[0,1]"'),
    # intervals (+2; one reuses merge_intervals)
    ("non_overlapping_intervals", "non-overlapping-intervals", "medium", "intervals",
     "Minimum removals so the rest are non-overlapping intervals.",
     '"[[1,2],[2,3],[3,4],[1,3]]"', "1"),
    ("merge_intervals", "merge-intervals-calendar-cleanup", "medium", "intervals",
     "Calendar cleanup: merge intervals that overlap on the schedule.",
     '"[[1,4],[2,3]]"', '"[[1,4]]"'),
    # backtrack (+4)
    ("combination_sum", "combination-sum", "medium", "backtracking",
     "All unique combos summing to target with reuse (combination sum).",
     '"[2,3,6,7]", 7', '"[[2,2,3],[7]]"'),
    ("generate_parentheses", "generate-parentheses", "medium", "backtracking",
     "Generate all well-formed parentheses strings (generate parentheses).",
     '"3"', '"((())),(()()),(())(),()(()),()()()"'),
    ("permutations", "permutations", "medium", "backtracking",
     "Return all permutations of the distinct numbers.",
     '"[1,2,3]"', '"[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]"'),
    ("subsets", "subsets", "medium", "backtracking",
     "Return all subsets of the set (subsets / power set).",
     '"[1,2,3]"', '"[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]"'),
]


def _build_extra_seed_questions() -> list:
    """Expand _EXTRA_SEED_SPECS into full Question payloads.

    Titles, starter stubs and solutions come from the reference catalog so
    every seed resolves; raises KeyError at import for unknown algorithm
    keys (fail fast instead of seeding unresolvable rows).
    """
    from app.services.reference_solutions import get_reference_solution

    seeds = []
    for algo, qid, difficulty, category, desc, ex_in, ex_out in _EXTRA_SEED_SPECS:
        entry = get_reference_solution(algo)
        if entry is None:
            raise KeyError(f"unknown reference algorithm in seed specs: {algo}")
        fn = entry["function"]
        sig = ", ".join(entry["signature"])
        seeds.append(
            {
                "id": qid,
                "title": entry["title"],
                "difficulty": difficulty,
                "category": category,
                "company_tags": [],
                "description": desc,
                "starter": {
                    "python": f"def {fn}({sig}):\n    pass",
                    "javascript": f"function {fn}() {{}}",
                    "java": (
                        "class Solution { public Object "
                        f"{fn}() {{ return null; }} }}"
                    ),
                },
                "examples": [{"input": ex_in, "output": ex_out}],
                "test_cases": [
                    {"input": ex_in, "expected_output": ex_out, "hidden": False}
                ],
                "hints": ["Think through the optimal approach first."],
                "solution": entry["code"],
                "time_complexity": "O(n)",
                "space_complexity": "O(n)",
                "constraints": [],
                "is_interactive": False,
            }
        )
    return seeds


_TEST_QUESTIONS.extend(_build_extra_seed_questions())


async def _seed_questions() -> int:
    """Seed a minimal inline question bank into the test database if empty.

    The test database starts empty (the app is fully DB-backed); these inline
    fixtures are defined in code — not read from any data file — so the API and
    integration tests have data to query. Unit SQL repository tests clean tables
    (test_db) for isolation.
    """
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base, QuestionORM

    engine = create_async_engine(
        _test_db_url(), poolclass=NullPool, **_test_engine_kwargs()
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    count = 0
    async with async_session() as session:
        from sqlalchemy import select

        # Idempotent PER-QUESTION upsert (not all-or-nothing): other test
        # files may leave orphan question rows behind, and an "only if table
        # empty" guard made the fixture bank order-dependent (latent flake
        # surfaced by the rescue-queue tests, Aug 23).
        existing = set((await session.execute(select(QuestionORM.id))).scalars().all())
        if len(existing) < len(_TEST_QUESTIONS):
            from app.models.schemas import Question

            for item in _TEST_QUESTIONS:
                try:
                    q = Question(**item)
                except Exception:
                    continue
                if q.id in existing:
                    continue
                session.add(
                    QuestionORM(
                        id=q.id,
                        title=q.title,
                        difficulty=q.difficulty.value,
                        category=q.category,
                        company_tags=q.company_tags,
                        description=q.description,
                        starter_code=q.starter.model_dump()
                        if hasattr(q.starter, "model_dump")
                        else q.starter,
                        examples=[
                            e.model_dump() if hasattr(e, "model_dump") else e
                            for e in q.examples
                        ],
                        test_cases=[
                            tc.model_dump() if hasattr(tc, "model_dump") else tc
                            for tc in q.test_cases
                        ],
                        hints=q.hints,
                        solution=q.solution,
                        time_complexity=q.time_complexity,
                        space_complexity=q.space_complexity,
                        constraints=q.constraints,
                        is_interactive=1 if q.is_interactive else 0,
                    )
                )
                count += 1
            await session.commit()
    await engine.dispose()
    return count


def _seed_questions_sync() -> int:
    """Sync variant of _seed_questions (only safe outside a running loop)."""
    return asyncio.run(_seed_questions())


@pytest.fixture(scope="session", autouse=True)
def seed_test_questions():
    """Seed the sample question bank once per session.

    Sync fixture using ``asyncio.run`` so it never depends on the (function-
    scoped) pytest-asyncio event loop, avoiding ScopeMismatch when the app
    itself spins up its own loop.
    """
    _seed_questions_sync()
    yield


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for asynchronous testing."""
    await _seed_questions()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_db():
    """Provide an isolated DB-backed session for SQL repository tests.

    Cleans all tables before each test so tests do not interfere with each
    other or with the running application's database. Works on
    PostgreSQL/Supabase (search_path points at the `codecoach_test` schema).
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from app.models.orm import Base

    db_url = _test_db_url()
    test_engine = create_async_engine(
        db_url, poolclass=NullPool, **_test_engine_kwargs()
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"DELETE FROM {table.name}"))
            if hasattr(table.c, "id") and db_url.startswith("postgresql+asyncpg"):
                await conn.execute(
                    text(f"ALTER SEQUENCE IF EXISTS {table.name}_id_seq RESTART WITH 1")
                )

    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await test_engine.dispose()
    await _seed_questions()


@pytest.fixture
def mock_piston_service():
    """Mock Piston service for testing."""

    class MockPistonService:
        async def execute(
            self, language: str, code: str, stdin: str = "", version: str = None
        ):
            """Mock execution returning ExecutionResult."""
            from app.ports.code_executor import ExecutionResult

            if "error" in code.lower():
                return ExecutionResult(
                    exit_code=1, stderr="SyntaxError: invalid syntax"
                )
            return ExecutionResult(stdout="Hello, World!\n", exit_code=0)

        def validate_code(self, language: str, code: str):
            """Mock code validation."""
            is_valid = "error" not in code.lower()
            return {
                "valid": is_valid,
                "warnings": ["Consider adding type hints"]
                if language == "python"
                else [],
                "errors": ["Syntax error on line 1"] if not is_valid else [],
            }

        async def get_runtimes(self):
            """Mock runtime information."""
            return [
                {
                    "language": "python",
                    "version": "3.11.0",
                    "aliases": ["py", "python3"],
                    "runtime": "cpython",
                }
            ]

    return MockPistonService


@pytest.fixture
def mock_question_bank():
    """Mock QuestionBank for testing."""
    from unittest.mock import AsyncMock

    bank = AsyncMock(spec=QuestionBank)
    return bank


@pytest.fixture
def test_env_vars():
    """Set up test environment variables."""
    env_vars = {
        "GROQ_API_KEY": "test_groq_key",
        "PISTON_API_URL": "https://emkc.org/api/v2/piston",
        "QUESTIONS_FILE_PATH": "tests/fixtures/test_questions.json",
        "RATE_LIMIT_PER_MINUTE": "100",
        "RATE_LIMIT_PER_HOUR": "1000",
        "ENVIRONMENT": "testing",
        "JWT_SECRET_KEY": "test-secret-key-for-testing-only-32chars!!",
        "COACH_RATE_LIMIT": "1000/minute",
        "RUN_RATE_LIMIT": "1000/minute",
    }

    # Store original values
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value

    yield

    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def admin_headers(test_client: TestClient) -> dict:
    """Return Authorization headers for an admin user.

    Registers (or logs in) a fixed admin user and promotes it to admin by
    updating the users table directly, mirroring test_admin_curriculum_crud.py.
    """
    res = test_client.post(
        "/api/auth/register",
        json={
            "username": "auditadmin",
            "email": "auditadmin@test.com",
            "password": "testpass123",
        },
    )
    if res.status_code != 201:
        res = test_client.post(
            "/api/auth/login",
            json={"username": "auditadmin", "password": "testpass123"},
        )
    token = res.json()["access_token"]

    async def _promote_admin() -> None:
        from sqlalchemy import text as sa_text
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from sqlalchemy.pool import NullPool

        engine = create_async_engine(
            _test_db_url(), poolclass=NullPool, **_test_engine_kwargs()
        )
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            await session.execute(
                sa_text("UPDATE users SET role='admin' WHERE username=:u"),
                {"u": "auditadmin"},
            )
            await session.commit()
        await engine.dispose()

    asyncio.run(_promote_admin())

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_question_data():
    """Provide sample question data for testing."""
    return {
        "id": "test-question",
        "title": "Test Question",
        "difficulty": "easy",
        "category": "arrays",
        "company_tags": ["TestCompany"],
        "description": "This is a test question for unit testing.",
        "starter": {"python": "def test_function(input):\n    pass"},
        "examples": [
            {
                "input": "input = [1, 2, 3]",
                "output": "6",
                "explanation": "Sum of array elements",
            }
        ],
        "test_cases": [
            {
                "input": "[1, 2, 3]",
                "expected_output": "6",
                "description": "Basic test case",
                "hidden": False,
            }
        ],
        "hints": ["Consider using a loop", "Think about edge cases"],
        "solution": "Use a simple loop to sum the elements",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "constraints": ["1 <= len(array) <= 1000", "-1000 <= array[i] <= 1000"],
    }


@pytest.fixture
def sample_coaching_request():
    """Provide sample coaching request data."""
    return {
        "problem": "Given an array of integers, find the maximum sum of any contiguous subarray.",
        "code": "def max_subarray_sum(nums):\n    max_sum = nums[0]\n    current_sum = nums[0]\n    \n    for i in range(1, len(nums)):\n        current_sum = max(nums[i], current_sum + nums[i])\n        max_sum = max(max_sum, current_sum)\n    \n    return max_sum",
        "language": "python",
        "message": "Can you review my solution and suggest improvements?",
        "mode": "review",
        "difficulty": "medium",
    }


@pytest.fixture
def sample_code_execution_request():
    """Provide sample code execution request data."""
    return {
        "language": "python",
        "code": "print('Hello, World!')\nprint(sum([1, 2, 3, 4, 5]))",
        "stdin": "",
        "version": "3.11.0",
    }


@pytest.fixture
def temp_questions_file():
    """Create a temporary questions file for testing."""
    test_questions = [
        {
            "id": "test-question-1",
            "title": "Test Question 1",
            "difficulty": "easy",
            "category": "arrays",
            "company_tags": ["TestCompany"],
            "description": "Test description 1",
            "starter": {"python": "def test1(input):\n    pass"},
            "examples": [{"input": "[1,2,3]", "output": "6", "explanation": "Sum"}],
            "test_cases": [
                {"input": "[1,2,3]", "expected_output": "6", "description": "Test"}
            ],
        },
        {
            "id": "test-question-2",
            "title": "Test Question 2",
            "difficulty": "medium",
            "category": "strings",
            "company_tags": ["AnotherCompany"],
            "description": "Test description 2",
            "starter": {"python": "def test2(input):\n    pass"},
            "examples": [
                {"input": "'hello'", "output": "'olleh'", "explanation": "Reverse"}
            ],
            "test_cases": [
                {
                    "input": "'hello'",
                    "expected_output": "'olleh'",
                    "description": "Test",
                }
            ],
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(test_questions, f, indent=2)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture(autouse=True)
def _reset_rate_limiter_state():
    """Give every test a clean slowapi rate-limit slate.

    slowapi's in-memory storage is process-global; without a reset, per-IP
    counters leak across tests and make later tests fail spuriously once the
    limit window is exhausted (e.g. question reads at 100/minute).
    """
    yield
    app.state.limiter.reset()
