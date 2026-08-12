"""Deterministic, category-aware company tag assignment.

The hand-authored questions share a near-identical tag set (Amazon/Google/
Microsoft on almost everything), which makes the company filter useless. This
module reassigns 1-3 realistic companies per question deterministically from
its category's pool, so every company appears a reasonable number of times and
filters return varied results.
"""

from __future__ import annotations

from typing import Dict, List

# Category -> pool of companies that realistically ask that kind of problem.
_POOLS: Dict[str, List[str]] = {
    "Arrays & Hashing": ["Amazon", "Google", "Microsoft", "Adobe", "Goldman Sachs"],
    "Two Pointers": ["Amazon", "Google", "Apple", "Bloomberg"],
    "Sliding Window": ["Amazon", "Google", "Meta", "Bloomberg"],
    "Binary Search": ["Amazon", "Google", "Microsoft", "Bloomberg"],
    "Stack & Queue": ["Amazon", "Microsoft", "Meta", "Goldman Sachs"],
    "Linked Lists": ["Amazon", "Microsoft", "Meta", "Adobe"],
    "Trees & Recursion": ["Amazon", "Google", "Microsoft", "Apple"],
    "Graphs": ["Amazon", "Google", "Microsoft", "Uber", "Lyft", "Airbnb"],
    "Heaps & Priority Queues": ["Amazon", "Google", "Apple", "Palantir"],
    "Intervals": ["Amazon", "Google", "Uber", "Lyft"],
    "Greedy": ["Amazon", "Google", "Microsoft", "Goldman Sachs"],
    "Dynamic Programming": ["Amazon", "Google", "Microsoft", "Meta"],
    "Backtracking": ["Amazon", "Microsoft", "Meta", "Adobe"],
    "Strings": ["Amazon", "Google", "Microsoft", "Apple", "Bloomberg"],
    "Bit Manipulation": ["Amazon", "Google", "Microsoft", "Qualcomm"],
    "Math": ["Amazon", "Microsoft", "Goldman Sachs"],
}


def _hash_id(qid: str) -> int:
    h = 0
    for ch in qid:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


def assign_companies(specs) -> None:
    """Mutate each spec's companies in place with a deterministic tag set."""
    for spec in specs:
        pool = _POOLS.get(spec.category, ["Amazon", "Google", "Microsoft"])
        h = _hash_id(spec.id)
        count = 1 + (h % 3)  # 1-3 tags
        selected = []
        for i in range(min(count, len(pool))):
            selected.append(pool[(h + i * 7) % len(pool)])
        tags = sorted(set(selected))
        spec.companies = tags
