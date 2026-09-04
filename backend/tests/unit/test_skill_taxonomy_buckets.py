"""NeetCode bucket alignment (Issue #135).

The roadmap track must expose NeetCode-style buckets: tries, intervals,
math-geometry, and a 1-D/2-D DP split. The monolithic ``dynamic-programming``
slug must disappear from both taxonomy and mappings.
"""

from app.models.skill_graph_schemas import SkillKind
from app.services import skill_taxonomy
from app.services.skill_taxonomy import QUESTION_SKILLS, SKILLS

EXPECTED_ORDER = (
    "arrays",
    "strings",
    "hash-maps",
    "two-pointers",
    "sliding-window",
    "stacks-queues",
    "heaps",
    "recursion",
    "backtracking",
    "sorting",
    "searching",
    "linked-lists",
    "trees",
    "tries",
    "graphs",
    "dp-1d",
    "dp-2d",
    "greedy",
    "intervals",
    "bit-manipulation",
    "math-geometry",
)


class TestNeetCodeBuckets:
    def test_new_roadmap_skills_exist(self):
        by_slug = {s.slug: s for s in SKILLS}
        for slug in ("tries", "intervals", "math-geometry", "dp-1d", "dp-2d"):
            assert slug in by_slug, f"missing roadmap skill '{slug}'"
            assert by_slug[slug].kind == SkillKind.ROADMAP

    def test_monolith_dp_removed(self):
        assert "dynamic-programming" not in {s.slug for s in SKILLS}
        stale = [
            q
            for q, maps in QUESTION_SKILLS.items()
            for m in maps
            if m.skill_slug == "dynamic-programming"
        ]
        assert not stale, f"mappings still reference monolith DP: {stale}"

    def test_roadmap_order_is_explicit_neetcode_order(self):
        assert tuple(skill_taxonomy.ROADMAP_ORDER) == EXPECTED_ORDER
        assert set(skill_taxonomy.ROADMAP_ORDER) == set(
            skill_taxonomy.ROADMAP_SKILL_SLUGS
        )

    def test_interval_questions_mapped_to_intervals(self):
        for q in ("merge-intervals", "non-overlapping-intervals", "car-fleet"):
            slugs = {m.skill_slug for m in QUESTION_SKILLS[q]}
            assert "intervals" in slugs, f"{q} not mapped to intervals: {slugs}"
            assert "sorting" not in slugs, f"{q} still mapped to sorting"

    def test_dp_split_classics(self):
        dp1 = {
            q
            for q, maps in QUESTION_SKILLS.items()
            if any(m.skill_slug == "dp-1d" for m in maps)
        }
        assert {
            "climbing-stairs",
            "coin-change",
            "house-robber",
            "word-break",
            "decode-ways",
            "longest-increasing-subsequence",
            "maximum-product-subarray",
        } <= dp1
        dp2 = {
            q
            for q, maps in QUESTION_SKILLS.items()
            if any(m.skill_slug == "dp-2d" for m in maps)
        }
        assert {"edit-distance", "burst-balloons"} <= dp2
