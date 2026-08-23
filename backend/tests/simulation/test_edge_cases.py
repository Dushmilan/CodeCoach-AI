"""System and data edge-case simulation tests.

These are not learner personalities — they exercise how the deterministic
engine + repository react to malformed, hostile, or unusual data.
"""

from __future__ import annotations

from datetime import timedelta


from app.models.skill_graph_schemas import (
    LearningEvent,
    LearningEventType,
    UserSkillState,
)
from app.services.skill_graph_rules import decay_state
from app.services.skill_taxonomy import SKILLS

from .event_sequences import T0, pass_evt
from .harness import build_seeded_repo


def _seeded_service():
    from app.services.skill_graph_service import SkillGraphService

    return SkillGraphService(repository=build_seeded_repo())


def _evt(user, etype, seq=0, question=None, skill_slug=None, meta=None):
    return LearningEvent(
        id=f"edge-{user}-{seq}",
        user_id=user,
        event_type=etype,
        question_id=question,
        skill_slug=skill_slug,
        metadata=meta or {},
        occurred_at=T0 + timedelta(hours=seq),
    )


class TestDuplicateEvents:
    def test_same_event_id_applied_once(self):
        import asyncio

        service = _seeded_service()
        evt = pass_evt(0, "u", "two-sum")

        r1 = asyncio.run(service.ingest_events([evt, evt, evt]))
        states = asyncio.run(service.repository.get_states("u"))
        assert r1.duplicate == 2
        assert states["hash-maps"].evidence_count == 1

    def test_duplicate_then_recompute_identical(self):
        """Ingest twice -> the second ingest is fully skipped, states stable."""
        import asyncio

        service = _seeded_service()
        evt = pass_evt(0, "u", "two-sum")

        asyncio.run(service.ingest_events([evt]))
        states_a = asyncio.run(service.repository.get_states("u"))

        asyncio.run(service.ingest_events([evt]))
        states_b = asyncio.run(service.repository.get_states("u"))

        assert states_a["hash-maps"].evidence_count == 1
        assert states_b["hash-maps"].evidence_count == 1


class TestOutOfOrderEvents:
    def test_review_before_submission_handled_safely(self):
        import asyncio

        from .event_sequences import review_evt

        service = _seeded_service()
        review = review_evt(0, "u", "hash-maps", passed=True)
        result = asyncio.run(service.ingest_events([review]))
        assert result.accepted == 1
        states = asyncio.run(service.repository.get_states("u"))
        assert "hash-maps" in states


class TestMissingMetadata:
    def test_event_without_question_or_skill_is_persisted_but_no_state(self):
        import asyncio

        service = _seeded_service()
        evt = _evt(
            "u", LearningEventType.SUBMISSION_PASSED, skill_slug=None, question=None
        )
        result = asyncio.run(service.ingest_events([evt]))
        assert result.accepted == 1
        states = asyncio.run(service.repository.get_states("u"))
        assert states == {}

    def test_event_without_id_skipped(self):
        import asyncio

        service = _seeded_service()
        evt = LearningEvent(
            id=None, user_id="u", event_type=LearningEventType.SUBMISSION_PASSED
        )
        result = asyncio.run(service.ingest_events([evt]))
        assert result.skipped == 1
        assert result.accepted == 0


class TestUnknownSkills:
    def test_unknown_skill_slug_ignored(self):
        import asyncio

        service = _seeded_service()
        evt = _evt(
            "u", LearningEventType.SUBMISSION_PASSED, skill_slug="quantum-computing"
        )
        result = asyncio.run(service.ingest_events([evt]))
        assert result.accepted == 1
        states = asyncio.run(service.repository.get_states("u"))
        assert "quantum-computing" not in states

    def test_unknown_question_creates_no_skills(self):
        import asyncio

        service = _seeded_service()
        evt = pass_evt(0, "u", "does-not-exist")
        result = asyncio.run(service.ingest_events([evt]))
        assert result.accepted == 1
        states = asyncio.run(service.repository.get_states("u"))
        assert states == {}


class TestInvalidScores:
    def test_mastery_stays_bounded_after_many_failures(self):
        import asyncio

        service = _seeded_service()
        events = []
        for i in range(200):
            events.append(
                _evt(
                    "u",
                    LearningEventType.SUBMISSION_FAILED,
                    seq=i,
                    question="two-sum",
                )
            )
        asyncio.run(service.ingest_events(events))
        states = asyncio.run(service.repository.get_states("u"))
        for state in states.values():
            assert 0.0 <= state.mastery_score <= 1.0
            assert 0.0 <= state.confidence <= 1.0


class TestEmptyHistory:
    def test_new_user_gets_valid_recommendations(self):
        import asyncio

        service = _seeded_service()
        recs = asyncio.run(service.get_recommendations("empty-user", limit=5))
        assert 1 <= len(recs) <= 5
        for rec in recs:
            assert rec.reason_text
            assert rec.skill_slug
            # References must be valid skill slugs.
            assert rec.skill_slug in {s.slug for s in SKILLS}

    def test_empty_graph_returns_empty_skills(self):
        import asyncio

        service = _seeded_service()
        graph = asyncio.run(service.get_graph("empty-user"))
        assert graph.skills == []


class TestDeletedHistory:
    def test_delete_resets_state_and_events(self):
        import asyncio

        service = _seeded_service()
        asyncio.run(service.ingest_events([pass_evt(0, "u", "two-sum")]))
        asyncio.run(service.delete_history("u"))

        states = asyncio.run(service.repository.get_states("u"))
        events = asyncio.run(service.repository.get_user_events("u"))
        assert states == {}
        assert events == []
        assert asyncio.run(service.get_graph("u")).skills == []

    def test_delete_does_not_affect_other_users(self):
        import asyncio

        service = _seeded_service()
        asyncio.run(service.ingest_events([pass_evt(0, "alice", "two-sum")]))
        asyncio.run(service.ingest_events([pass_evt(0, "bob", "two-sum")]))
        asyncio.run(service.delete_history("alice"))

        states_bob = asyncio.run(service.repository.get_states("bob"))
        assert "hash-maps" in states_bob
        assert states_bob["hash-maps"].evidence_count == 1


class TestTimezoneBoundary:
    def test_midnight_activity_reviewed_correctly(self):
        import asyncio

        service = _seeded_service()
        events = [
            pass_evt(0, "u", "two-sum"),
            pass_evt(1, "u", "two-sum"),
        ]
        asyncio.run(service.ingest_events(events))
        graph = asyncio.run(service.get_graph("u"))
        assert graph.skills


class TestLongInactive:
    def test_long_inactivity_decays_predictably(self):
        state = UserSkillState(
            user_id="u",
            skill_slug="hash-maps",
            mastery_score=0.8,
            confidence=0.7,
            evidence_count=5,
            last_seen_at=T0,
        )
        future = T0 + timedelta(days=120)
        decayed = decay_state(state, future)
        assert decayed.mastery_score < state.mastery_score
        assert decayed.mastery_score > 0.0
        # Status should drop below strong after 4+ months away.
        assert decayed.status.value != "strong"


class TestUnmappedQuestion:
    def test_unmapped_question_does_not_affect_graph(self):
        import asyncio

        service = _seeded_service()
        evt = _evt("u", LearningEventType.SUBMISSION_PASSED, question="unmapped-q")
        result = asyncio.run(service.ingest_events([evt]))
        assert result.accepted == 1
        graph = asyncio.run(service.get_graph("u"))
        assert graph.skills == []


class TestMalformedDiagnosis:
    def test_conflicting_diagnosis_does_not_crash_engine(self):
        import asyncio

        service = _seeded_service()
        events = [
            _evt(
                "u",
                LearningEventType.DIAGNOSIS_CREATED,
                seq=0,
                question="two-sum",
                meta={"skills": ["arrays", "not-a-skill"], "passed": "maybe"},
            ),
            pass_evt(1, "u", "two-sum"),
        ]
        result = asyncio.run(service.ingest_events(events))
        assert result.accepted == 2
        states = asyncio.run(service.repository.get_states("u"))
        assert states["hash-maps"].evidence_count >= 1


class TestPartialFailurePersistence:
    def test_foreign_user_event_rejected_when_pinned(self):
        import asyncio

        service = _seeded_service()
        events = [
            _evt(
                "u", LearningEventType.SUBMISSION_PASSED, seq=0, question="two-sum"
            ),
            _evt(
                "u2",
                LearningEventType.SUBMISSION_PASSED,
                seq=1,
                question="two-sum",
            ),
        ]
        # Second event belongs to a different user and must be rejected when
        # the caller pins user_id.
        result = asyncio.run(service.ingest_events(events, user_id="u"))
        assert result.invalid == 1
        assert result.accepted == 1


class TestConcurrentEvents:
    def test_interleaved_events_do_not_lose_updates(self):
        import asyncio

        service = _seeded_service()
        # Sequential simulation of concurrent interleaving: alternating users.
        for i in range(6):
            user = "u" if i % 2 == 0 else "u2"
            asyncio.run(service.ingest_events([pass_evt(i, user, "two-sum")]))

        states = asyncio.run(service.repository.get_states("u"))
        assert states["hash-maps"].evidence_count == 3
