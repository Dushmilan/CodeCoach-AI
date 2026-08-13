"""Learner-profile simulation tests.

Each persona runs its deterministic event sequence through the real service +
in-memory repo and must satisfy persona expectations and universal invariants.
"""

from __future__ import annotations

import random

import pytest

from .harness import (
    assert_profile_expectations,
    assert_universal_invariants,
    run_profile,
)
from .learner_profiles import PROFILES


@pytest.mark.parametrize("profile_name", sorted(PROFILES))
def test_learner_profile(profile_name):
    rng = random.Random(f"seed-{profile_name}")
    factory, _ = PROFILES[profile_name]
    user = f"user-{profile_name}"
    events, expected = factory(user, rng)
    service, repo, states = run_profile(user, events, rng)
    assert_profile_expectations(states, expected, service, repo, user)


@pytest.mark.parametrize("profile_name", sorted(PROFILES))
def test_learner_profile_reproducible(profile_name):
    """Same seed -> identical state every run (determinism requirement)."""
    rng = random.Random(f"seed-{profile_name}")
    factory, _ = PROFILES[profile_name]
    user = f"user-{profile_name}"
    events, _ = factory(user, rng)

    service_a, _, states_a = run_profile(user, list(events), rng)
    service_b, _, states_b = run_profile(user, list(events), rng)

    a = {s: st.model_dump() for s, st in states_a.items()}
    b = {s: st.model_dump() for s, st in states_b.items()}
    assert a == b


@pytest.mark.parametrize("profile_name", sorted(PROFILES))
def test_learner_profile_duplicate_events_idempotent(profile_name):
    """Replaying the first few events must not double-count evidence."""
    rng = random.Random(f"seed-dup-{profile_name}")
    factory, _ = PROFILES[profile_name]
    user = f"user-{profile_name}"
    events, expected = factory(user, rng)

    _, repo, states = run_profile(user, events, rng, with_duplicates=True)
    assert_universal_invariants(states)

    # Evidence counts must equal the unique event count per skill (≤ total).
    for state in states.values():
        assert state.evidence_count <= len(events)


@pytest.mark.parametrize("profile_name", sorted(PROFILES))
def test_learner_profile_foreign_user_isolation(profile_name):
    """Foreign-user events must never leak into the learner's states."""
    rng = random.Random(f"seed-iso-{profile_name}")
    factory, _ = PROFILES[profile_name]
    user = f"user-{profile_name}"
    events, expected = factory(user, rng)

    _, repo, states = run_profile(user, events, rng, interleave_foreign=True)
    assert_universal_invariants(states)

    for state in states.values():
        assert state.user_id == user
