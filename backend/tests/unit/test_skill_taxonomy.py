"""Unit tests for the skill taxonomy (F3: full question-bank coverage).

"Practice Next" can only recommend questions that carry a skill mapping, so
the taxonomy must cover the whole live bank and must never reference dead
question ids or unknown skills. The live inventory snapshot
(``tests/fixtures/live_question_ids.json``) makes coverage drift loud: adding
a question to the bank without mapping it fails these tests.
"""

import json
from pathlib import Path

import pytest

from app.services.skill_taxonomy import QUESTION_SKILLS, SKILLS

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "live_question_ids.json"


@pytest.fixture(scope="module")
def live_question_ids() -> list[str]:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return sorted(data["question_ids"])


def _all_mappings():
    for question_id, mappings in QUESTION_SKILLS.items():
        for m in mappings:
            yield question_id, m


class TestTaxonomyIntegrity:
    def test_every_mapped_skill_slug_exists(self):
        known = {s.slug for s in SKILLS}
        bad = {m.skill_slug for _, m in _all_mappings() if m.skill_slug not in known}
        assert not bad, f"mappings reference unknown skills: {sorted(bad)}"

    def test_prerequisites_exist(self):
        known = {s.slug for s in SKILLS}
        bad = {
            pre
            for s in SKILLS
            for pre in (s.prerequisite_ids or [])
            if pre not in known
        }
        assert not bad, f"skills declare unknown prerequisites: {sorted(bad)}"

    def test_no_prerequisite_cycles(self):
        prereq = {s.slug: set(s.prerequisite_ids or []) for s in SKILLS}

        def reaches(start: str, target: str, seen: frozenset) -> bool:
            if target in prereq[start]:
                return True
            for nxt in prereq[start]:
                if nxt in seen:
                    continue
                if reaches(nxt, target, seen | {nxt}):
                    return True
            return False

        for slug in prereq:
            assert not reaches(slug, slug, frozenset()), (
                f"prerequisite cycle involving '{slug}'"
            )

    @pytest.mark.parametrize(
        "question_id,mappings",
        sorted(QUESTION_SKILLS.items()),
        ids=sorted(QUESTION_SKILLS.keys()),
    )
    def test_weights_sum_to_one(self, question_id, mappings):
        total = sum(m.weight for m in mappings)
        assert pytest.approx(total, abs=1e-6) == 1.0, (
            f"{question_id} weights sum to {total}"
        )
        assert all(0 < m.weight <= 1.0 for m in mappings)

    def test_unique_question_id_and_no_self_duplicates(self):
        # Each question appears once as a key; no duplicate skill per question.
        for question_id, mappings in QUESTION_SKILLS.items():
            slugs = [m.skill_slug for m in mappings]
            assert len(slugs) == len(set(slugs)), (
                f"{question_id} maps the same skill twice"
            )


class TestFullCoverage:
    def test_every_mapping_resolves_to_a_live_question(self, live_question_ids):
        live = set(live_question_ids)
        dead = sorted(set(QUESTION_SKILLS.keys()) - live)
        assert not dead, (
            "QUESTION_SKILLS contains ids that do not exist in the live bank "
            "(dead mappings): "
            f"{dead}"
        )

    def test_every_live_question_has_at_least_one_skill(self, live_question_ids):
        unmapped = [q for q in live_question_ids if q not in QUESTION_SKILLS]
        assert not unmapped, (
            f"{len(unmapped)} live questions have NO skill mapping and are "
            f"invisible to Practice Next: {unmapped[:20]}..."
        )

    def test_snapshot_covers_a_realistic_bank(self, live_question_ids):
        # Guard against an accidentally truncated/empty fixture silently
        # weakening the two tests above.
        assert len(live_question_ids) >= 100, (
            f"live inventory snapshot only has {len(live_question_ids)} ids; "
            "regenerate tests/fixtures/live_question_ids.json"
        )
