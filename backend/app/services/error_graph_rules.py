"""Deterministic derivation of the per-user error graph (mistake-memory #1).

Pure functions only — no I/O. Groups a learner's failed submissions by their
stable error signature and answers three questions per signature: how often
it recurred, which questions it haunted, and whether every affected question
was eventually solved *after* its last occurrence ("resolved").

The concept/skill dimension of the graph already lives in the skill-graph
module (per-skill mastery from SUBMISSION_* events); this module owns the
signature dimension. Persistence lives in repositories; orchestration in
services.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Sequence

from app.models.mistake_schemas import ErrorSignatureNode
from app.models.submission_schemas import Submission


def derive_error_graph(
    submissions: Sequence[Submission],
) -> List[ErrorSignatureNode]:
    """Group failed submissions into ranked, resolution-aware signature nodes.

    Ranking: most occurrences first, then most recently seen, then
    alphabetically for stability.
    """
    failures_by_signature: Dict[str, List[Submission]] = defaultdict(list)
    for sub in submissions:
        if not sub.passed and sub.error_signature:
            failures_by_signature[sub.error_signature].append(sub)

    passing_times_by_question: Dict[str, List] = defaultdict(list)
    for sub in submissions:
        if sub.passed:
            passing_times_by_question[sub.question_id].append(sub.created_at)

    nodes: List[ErrorSignatureNode] = []
    for signature, failures in failures_by_signature.items():
        last_failure_by_question: Dict[str, object] = {}
        for failure in failures:
            known = last_failure_by_question.get(failure.question_id)
            if known is None or failure.created_at > known:
                last_failure_by_question[failure.question_id] = failure.created_at

        resolved = all(
            any(
                passed_at > last_failure_at
                for passed_at in passing_times_by_question.get(question_id, [])
            )
            for question_id, last_failure_at in last_failure_by_question.items()
        )

        seen_times = [f.created_at for f in failures]
        nodes.append(
            ErrorSignatureNode(
                signature=signature,
                occurrences=len(failures),
                questions=sorted(last_failure_by_question),
                first_seen_at=min(seen_times),
                last_seen_at=max(seen_times),
                resolved=resolved,
            )
        )

    # Stable multi-key ranking via successive stable sorts (last key wins).
    nodes.sort(key=lambda n: n.signature)
    nodes.sort(key=lambda n: n.last_seen_at, reverse=True)
    nodes.sort(key=lambda n: n.occurrences, reverse=True)
    return nodes
