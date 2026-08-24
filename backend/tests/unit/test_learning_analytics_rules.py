from datetime import datetime, timedelta, timezone

from app.models.submission_schemas import Submission
from app.services.learning_analytics_rules import derive_signals
from app.services.skill_taxonomy import QUESTION_SKILL_MAP

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def _sub(id, qid, passed, sig, days_ago=0):
    return Submission(
        id=id,
        user_id="u1",
        question_id=qid,
        code="c",
        language="python",
        passed=passed,
        error_signature=sig,
        attempt_index=0,
        created_at=NOW - timedelta(days=days_ago),
    )


def test_empty_returns_no_signals():
    assert derive_signals([], now=NOW) == []


def test_single_failure_no_plateau():
    subs = [_sub("s1", "two-sum", False, "expected 1 got 0", 1)]
    assert derive_signals(subs, now=NOW) == []


def test_three_failures_same_skill_no_pass_is_plateau():
    # two-sum maps to arrays/hash-table per skill_taxonomy; pick a recursion-heavy question
    # Use "invert-binary-tree" which maps to recursion (0.2) + trees (0.8)
    qid = "invert-binary-tree"
    assert "recursion" in dict(QUESTION_SKILL_MAP[qid])
    subs = [
        _sub("s1", qid, False, "sig A", 1),
        _sub("s2", qid, False, "sig A", 2),
        _sub("s3", qid, False, "sig B", 3),
    ]
    sigs = derive_signals(subs, now=NOW)
    # invert-binary-tree maps to trees+recursion, both plateaus; assert recursion present
    assert any(s.skill == "recursion" for s in sigs)
    rec = [s for s in sigs if s.skill == "recursion"][0]
    assert rec.type == "plateau"
    assert "plateau" in rec.title.lower()


def test_plateau_cleared_by_pass_in_window():
    qid = "invert-binary-tree"
    subs = [
        _sub("s1", qid, False, "sig A", 1),
        _sub("s2", qid, False, "sig A", 2),
        _sub("s3", qid, False, "sig A", 3),
        _sub("s4", qid, True, None, 0),  # pass after failures
    ]
    assert derive_signals(subs, now=NOW) == []


def test_outside_window_not_counted():
    qid = "invert-binary-tree"
    subs = [
        _sub("s1", qid, False, "sig A", 8),  # outside 7d window
        _sub("s2", qid, False, "sig A", 9),
        _sub("s3", qid, False, "sig A", 10),
    ]
    assert derive_signals(subs, now=NOW) == []


def test_ranking_most_failures_first():
    q1 = "invert-binary-tree"  # recursion
    q2 = "two-sum"  # arrays
    subs = [
        _sub("s1", q1, False, "sig A", 1),
        _sub("s2", q1, False, "sig A", 2),
        _sub("s3", q1, False, "sig A", 3),
        _sub("s4", q1, False, "sig A", 4),
        _sub("s5", q2, False, "sig B", 1),
        _sub("s6", q2, False, "sig B", 2),
        _sub("s7", q2, False, "sig B", 3),
    ]
    sigs = derive_signals(subs, now=NOW)
    assert [s.skill for s in sigs][0] == "recursion"  # 4 > 3
