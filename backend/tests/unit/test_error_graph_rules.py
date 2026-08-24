"""Unit tests for per-user error-graph derivation (mistake-memory #1).

The error graph groups a user's own failed submissions by error signature:
how often it recurred, on which questions, when it was last seen, and whether
every affected question was eventually solved *after* the last occurrence.
"""

from datetime import datetime, timedelta, timezone

from app.models.submission_schemas import Submission
from app.services.error_graph_rules import derive_error_graph

BASE = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)


def _sub(
    n: int,
    *,
    question_id: str,
    passed: bool,
    signature: str | None = None,
) -> Submission:
    return Submission(
        id=f"s-{n}",
        user_id="user-1",
        question_id=question_id,
        code="x",
        language="python",
        passed=passed,
        error_signature=signature,
        attempt_index=n,
        created_at=BASE + timedelta(hours=n),
    )


class TestEmptyAndDegenerateHistory:
    def test_empty_history_yields_empty_graph(self):
        assert derive_error_graph([]) == []

    def test_passing_submissions_never_form_nodes(self):
        nodes = derive_error_graph([_sub(0, question_id="q1", passed=True)])
        assert nodes == []

    def test_failures_without_signature_are_ignored(self):
        nodes = derive_error_graph([_sub(0, question_id="q1", passed=False)])
        assert nodes == []


class TestGrouping:
    def test_same_signature_across_questions_is_grouped(self):
        subs = [
            _sub(0, question_id="q2", passed=False, signature="expected True"),
            _sub(1, question_id="q1", passed=False, signature="expected True"),
            _sub(2, question_id="q1", passed=False, signature="expected True"),
        ]
        nodes = derive_error_graph(subs)

        assert len(nodes) == 1
        node = nodes[0]
        assert node.signature == "expected True"
        assert node.occurrences == 3
        assert node.questions == ["q1", "q2"]
        assert node.first_seen_at == BASE
        assert node.last_seen_at == BASE + timedelta(hours=2)

    def test_distinct_signatures_get_distinct_nodes(self):
        subs = [
            _sub(0, question_id="q1", passed=False, signature="sig-a"),
            _sub(1, question_id="q1", passed=False, signature="sig-b"),
        ]
        nodes = derive_error_graph(subs)
        assert {n.signature for n in nodes} == {"sig-a", "sig-b"}


class TestResolution:
    def test_pass_after_last_occurrence_resolves_the_bug(self):
        subs = [
            _sub(0, question_id="q1", passed=False, signature="sig"),
            _sub(1, question_id="q1", passed=True),  # solved after the failure
        ]
        nodes = derive_error_graph(subs)
        assert nodes[0].resolved is True

    def test_regressed_bug_is_not_resolved(self):
        subs = [
            _sub(0, question_id="q1", passed=False, signature="sig"),
            _sub(1, question_id="q1", passed=True),  # solved once...
            _sub(2, question_id="q1", passed=False, signature="sig"),  # ...regressed
        ]
        nodes = derive_error_graph(subs)
        assert nodes[0].resolved is False

    def test_resolved_requires_every_affected_question(self):
        subs = [
            _sub(0, question_id="q1", passed=False, signature="sig"),
            _sub(1, question_id="q2", passed=False, signature="sig"),
            _sub(2, question_id="q1", passed=True),  # q1 solved, q2 never
        ]
        nodes = derive_error_graph(subs)
        assert nodes[0].resolved is False


class TestRanking:
    def test_most_recurring_signature_ranks_first(self):
        subs = [
            _sub(0, question_id="q1", passed=False, signature="rare"),
            _sub(1, question_id="q1", passed=False, signature="common"),
            _sub(2, question_id="q1", passed=False, signature="common"),
        ]
        nodes = derive_error_graph(subs)
        assert [n.signature for n in nodes] == ["common", "rare"]

    def test_tie_on_occurrences_ranks_most_recent_first(self):
        subs = [
            _sub(0, question_id="q1", passed=False, signature="old"),
            _sub(5, question_id="q2", passed=False, signature="fresh"),
        ]
        nodes = derive_error_graph(subs)
        assert [n.signature for n in nodes] == ["fresh", "old"]

    def test_full_tie_breaks_alphabetically_for_stability(self):
        subs = [
            _sub(0, question_id="q1", passed=False, signature="b-sig"),
            _sub(0, question_id="q1", passed=False, signature="a-sig"),
        ]
        nodes = derive_error_graph(subs)
        assert [n.signature for n in nodes] == ["a-sig", "b-sig"]
