"""Shared harness for the learner-profile simulation.

Ingests a profile's deterministic event sequence through the real
``SkillGraphService`` + in-memory repository and asserts the profile's
expectations, plus universal invariants (bounds, idempotency, isolation).
"""

from __future__ import annotations

import asyncio
import random
from typing import Dict, List, Tuple


from app.models.skill_graph_schemas import (
    LearningEvent,
    UserSkillState,
)
from app.services.skill_graph_service import SkillGraphService
from app.services.skill_taxonomy import SKILLS, QUESTION_SKILLS

from .in_memory_repo import InMemorySkillGraphRepository
from .event_sequences import Q_TWO_SUM


def build_seeded_repo() -> InMemorySkillGraphRepository:
    """Build an in-memory repo seeded with the full taxonomy."""
    repo = InMemorySkillGraphRepository()
    repo.seed_skills(list(SKILLS))
    repo.seed_question_skills(
        [qs for mappings in QUESTION_SKILLS.values() for qs in mappings]
    )
    return repo


def _build_repo_and_service() -> Tuple[InMemorySkillGraphRepository, SkillGraphService]:
    repo = build_seeded_repo()
    return repo, SkillGraphService(repository=repo)


def run_profile(
    user: str,
    events: List[LearningEvent],
    rng: random.Random,
    with_duplicates: bool = False,
    interleave_foreign: bool = False,
) -> Tuple[SkillGraphService, InMemorySkillGraphRepository, Dict[str, UserSkillState]]:

    repo, service = _build_repo_and_service()

    events_to_send = list(events)
    if with_duplicates:
        events_to_send = events_to_send + [e for e in events[:3]]
    if interleave_foreign:
        foreign = [pass_evt_for("foreign-user", Q_TWO_SUM, idx) for idx in range(3)]
        events_to_send = (
            events_to_send[: len(events_to_send) // 2]
            + foreign
            + events_to_send[len(events_to_send) // 2 :]
        )

    asyncio.run(service.ingest_events(events_to_send))
    states = asyncio.run(repo.get_states(user))
    return service, repo, states


def pass_evt_for(user: str, question: str, seq: int) -> LearningEvent:
    from datetime import datetime, timezone

    from app.models.skill_graph_schemas import LearningEventType

    return LearningEvent(
        id=f"foreign-{user}-{seq}",
        user_id=user,
        event_type=LearningEventType.SUBMISSION_PASSED,
        question_id=question,
        occurred_at=datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
    )


def assert_universal_invariants(
    states: Dict[str, UserSkillState],
    expected_skill: str | None = None,
) -> None:
    """Invariants that must hold for every profile."""
    for slug, state in states.items():
        assert 0.0 <= state.mastery_score <= 1.0, f"{slug} mastery out of range"
        assert 0.0 <= state.confidence <= 1.0, f"{slug} confidence out of range"
        assert state.evidence_count >= 0
        assert state.recent_error_count >= 0


def assert_profile_expectations(
    states: Dict[str, UserSkillState],
    expected: Dict[str, object],
    service: SkillGraphService,
    repo: InMemorySkillGraphRepository,
    user: str,
) -> None:
    assert_universal_invariants(states)

    if expected.get("no_failures"):
        for state in states.values():
            assert state.recent_error_count == 0, "abandoning must not record errors"

    for slug, spec in expected.get("skills", {}).items():
        state = states.get(slug)
        assert state is not None, f"expected skill state for {slug}"
        if spec.get("mastery_ge") is not None:
            assert state.mastery_score >= spec["mastery_ge"], (
                f"{slug} mastery {state.mastery_score} < {spec['mastery_ge']}"
            )
        if spec.get("mastery_lt") is not None:
            assert state.mastery_score < spec["mastery_lt"], (
                f"{slug} mastery {state.mastery_score} >= {spec['mastery_lt']}"
            )
        if spec.get("status") is not None:
            assert state.status == spec["status"], (
                f"{slug} status {state.status} != {spec['status']}"
            )
        if spec.get("errors_ge") is not None:
            assert state.recent_error_count >= spec["errors_ge"], (
                f"{slug} errors {state.recent_error_count} < {spec['errors_ge']}"
            )
        if spec.get("errors_eq") is not None:
            assert state.recent_error_count == spec["errors_eq"], (
                f"{slug} errors {state.recent_error_count} != {spec['errors_eq']}"
            )

    if expected.get("recommend_prereq"):
        import asyncio

        recs = asyncio.run(service.get_recommendations(user, limit=10))
        slugs = [r.skill_slug for r in recs]
        assert expected["recommend_prereq"] in slugs, (
            f"recommendations missing {expected['recommend_prereq']}: {slugs}"
        )
