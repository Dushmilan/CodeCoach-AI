"""Pure plateau derivation for learning-analytics (Ideas #1 residual)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Sequence

from app.models.analytics_schemas import AnalyticsSignal
from app.models.submission_schemas import Submission
from app.services.skill_taxonomy import QUESTION_SKILL_MAP

WINDOW_DAYS = 7
FAILURE_THRESHOLD = 3


def derive_signals(
    submissions: Sequence[Submission], *, now: datetime
) -> List[AnalyticsSignal]:
    cutoff = now - timedelta(days=WINDOW_DAYS)
    # windowed
    windowed = [s for s in submissions if s.created_at >= cutoff]
    # group by skill: map qid -> skills
    by_skill: Dict[str, List[Submission]] = defaultdict(list)
    for s in windowed:
        skills = [slug for slug, _w in QUESTION_SKILL_MAP.get(s.question_id, [])]
        # fallback to category-as-skill via ORM? we don't have category here; skip if no map
        # For test stability, category fallback is handled in service layer where Question is available.
        # Here, only mapped questions count — unmapped are ignored (no false positives).
        for skill in skills:
            by_skill[skill].append(s)

    signals: List[AnalyticsSignal] = []
    for skill, subs in by_skill.items():
        failures = [x for x in subs if not x.passed]
        passes = [x for x in subs if x.passed]
        if len(failures) >= FAILURE_THRESHOLD and len(passes) == 0:
            # Check not resolved: no pass after last failure (already passes==0 in window, but keep for future relaxed rule)
            first = min(s.created_at for s in failures)
            last = max(s.created_at for s in failures)
            qids = sorted({s.question_id for s in failures})
            sigs = sorted({s.error_signature for s in failures if s.error_signature})
            signals.append(
                AnalyticsSignal(
                    type="plateau",
                    skill=skill,
                    title=f"{skill.replace('-', ' ').title()} plateau detected",
                    detail=f"{len(failures)} failures on {skill} in last {WINDOW_DAYS} days, 0 passes — try a 5-min refresher",
                    evidence={
                        "failures": len(failures),
                        "passes": 0,
                        "window_days": WINDOW_DAYS,
                        "question_ids": qids,
                        "signatures": sigs,
                    },
                    severity="warning",
                    first_seen_at=first,
                    last_seen_at=last,
                )
            )
    # stable ranking: alpha, then recency desc, then failures desc
    signals.sort(key=lambda s: s.skill)
    signals.sort(key=lambda s: s.last_seen_at, reverse=True)
    signals.sort(key=lambda s: s.evidence["failures"], reverse=True)
    return signals
