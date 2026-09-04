"""Roadmap vs supporting skill separation (Issue #134).

NeetCode-style roadmap must contain only interview-pattern skills. Supporting
/ cross-cutting skills stay in the DB + event system for analytics/coaching
but are excluded from roadmap ordering, progress totals, and primary
recommendations.
"""

from app.models.skill_graph_schemas import SkillKind
from app.services import skill_taxonomy


class TestRoadmapSeparation:
    def test_supporting_slugs_are_exactly_the_five(self):
        assert set(skill_taxonomy.SUPPORTING_SKILL_SLUGS) == {
            "programming-fundamentals",
            "debugging",
            "testing",
            "time-complexity",
            "space-complexity",
        }

    def test_supporting_skills_carry_supporting_kind(self):
        by_slug = {s.slug: s for s in skill_taxonomy.SKILLS}
        for slug in skill_taxonomy.SUPPORTING_SKILL_SLUGS:
            assert by_slug[slug].kind == SkillKind.SUPPORTING

    def test_roadmap_skills_exclude_supporting(self):
        roadmap_slugs = {s.slug for s in skill_taxonomy.roadmap_skills()}
        assert not (roadmap_slugs & set(skill_taxonomy.SUPPORTING_SKILL_SLUGS))
        # Core interview patterns stay on the roadmap.
        for slug in ("arrays", "hash-maps", "two-pointers", "graphs"):
            assert slug in roadmap_slugs

    def test_is_roadmap_skill_helper(self):
        assert skill_taxonomy.is_roadmap_skill("arrays") is True
        assert skill_taxonomy.is_roadmap_skill("debugging") is False


class TestRoadmapRecommendations:
    def _repo(self):
        from tests.simulation.in_memory_repo import InMemorySkillGraphRepository

        from app.services.skill_taxonomy import QUESTION_SKILLS, SKILLS

        repo = InMemorySkillGraphRepository()
        repo.seed_skills(list(SKILLS))
        repo.seed_question_skills(
            [m for mappings in QUESTION_SKILLS.values() for m in mappings]
        )
        return repo

    async def _recs(self, include_supporting: bool):
        from app.services.skill_graph_service import SkillGraphService

        service = SkillGraphService(repository=self._repo())
        return await service.get_recommendations(
            "u1", include_supporting=include_supporting
        )

    def test_default_recommendations_exclude_supporting(self):
        import asyncio

        recs = asyncio.run(self._recs(include_supporting=False))
        slugs = {r.skill_slug for r in recs}
        assert not (slugs & set(skill_taxonomy.SUPPORTING_SKILL_SLUGS))

    def test_opt_in_recommendations_can_include_supporting(self):
        import asyncio

        recs = asyncio.run(self._recs(include_supporting=True))
        # Full graph still knows supporting skills; at least the pipeline runs
        # without error and returns roadmap-first results.
        assert recs
