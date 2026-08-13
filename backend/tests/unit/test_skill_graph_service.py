"""Service + SQL repository tests for the Personal Skill Graph.

These exercise the real Supabase/PostgreSQL-backed repository (via the test_db
fixture) with the deterministic rules engine and service orchestration.
"""

import pytest
import pytest_asyncio

from app.models.orm import QuestionORM, SkillORM, UserORM
from app.models.skill_graph_schemas import LearningEventType, SkillStatus
from app.repositories.sql_skill_graph_repository import SqlSkillGraphRepository
from app.services.skill_graph_service import SkillGraphService
from app.services.skill_taxonomy import SKILLS, QUESTION_SKILLS


def _event(seq, user, etype, question, meta=None):
    from datetime import datetime as dt, timedelta, timezone

    from app.models.skill_graph_schemas import LearningEvent

    now = dt.now(timezone.utc)
    return LearningEvent(
        id=f"sql-{user}-{seq}",
        user_id=user,
        event_type=etype,
        question_id=question,
        metadata=meta or {},
        occurred_at=now - timedelta(minutes=10),
    )


def _pass(user, question, seq=0):
    return _event(seq, user, LearningEventType.SUBMISSION_PASSED, question)


@pytest_asyncio.fixture
async def seeded_db(test_db):
    session = test_db
    session.add(
        UserORM(
            id="u-skill",
            username="skilluser",
            email="skilluser@test.com",
            hashed_password="hash",
        )
    )
    session.add(
        UserORM(
            id="u-other",
            username="otheruser",
            email="other@test.com",
            hashed_password="hash",
        )
    )
    for skill in SKILLS:
        session.add(
            SkillORM(
                slug=skill.slug,
                name=skill.name,
                description=skill.description,
                parent_id=skill.parent_id,
                prerequisite_ids=skill.prerequisite_ids,
            )
        )
    for qid in QUESTION_SKILLS.keys():
        session.add(
            QuestionORM(
                id=qid,
                title=qid,
                difficulty="easy",
                category="arrays",
                company_tags=[],
                description="seed",
                starter_code={},
                examples=[],
                test_cases=[],
                hints=[],
                constraints=[],
                is_interactive=0,
            )
        )
    await session.commit()
    return session


@pytest_asyncio.fixture
async def skill_service(seeded_db):
    repo = SqlSkillGraphRepository(seeded_db)
    return SkillGraphService(repository=repo)


class TestSqlSkillGraphRepository:
    @pytest.mark.asyncio
    async def test_event_round_trip(self, seeded_db):
        repo = SqlSkillGraphRepository(seeded_db)
        evt = _pass("u-skill", "test-two-sum")
        await repo.save_event(evt)
        assert await repo.event_exists(evt.id)
        events = await repo.get_user_events("u-skill")
        assert len(events) == 1
        assert events[0].event_type == LearningEventType.SUBMISSION_PASSED
        assert events[0].metadata == {}

    @pytest.mark.asyncio
    async def test_state_round_trip(self, seeded_db):
        from app.models.skill_graph_schemas import UserSkillState

        repo = SqlSkillGraphRepository(seeded_db)
        state = UserSkillState(
            user_id="u-skill",
            skill_slug="arrays",
            mastery_score=0.5,
            confidence=0.4,
            evidence_count=3,
            recent_error_count=1,
            distinct_question_ids=["test-two-sum", "test-max-subarray"],
        )
        await repo.save_state(state)
        states = await repo.get_states("u-skill")
        assert "arrays" in states
        fetched = states["arrays"]
        assert fetched.mastery_score == 0.5
        assert fetched.confidence == 0.4
        assert fetched.distinct_question_ids == ["test-two-sum", "test-max-subarray"]

    @pytest.mark.asyncio
    async def test_delete_user_history(self, seeded_db):
        repo = SqlSkillGraphRepository(seeded_db)
        await repo.save_event(_pass("u-skill", "test-two-sum"))
        from app.models.skill_graph_schemas import UserSkillState

        await repo.save_state(
            UserSkillState(user_id="u-skill", skill_slug="arrays", mastery_score=0.5)
        )
        await repo.delete_user_history("u-skill")
        assert await repo.get_user_events("u-skill") == []
        assert await repo.get_states("u-skill") == {}

    @pytest.mark.asyncio
    async def test_user_isolation(self, seeded_db):
        repo = SqlSkillGraphRepository(seeded_db)
        await repo.save_event(_pass("u-skill", "test-two-sum"))
        assert await repo.get_user_events("u-other") == []


class TestSkillGraphServiceSql:
    @pytest.mark.asyncio
    async def test_ingest_updates_skill_state(self, skill_service):
        from app.services.skill_taxonomy import QUESTION_SKILLS

        # Need question-skill mappings seeded for attribution.
        from app.models.orm import QuestionSkillORM

        repo = skill_service.repository
        for question_id, mappings in QUESTION_SKILLS.items():
            for m in mappings:
                repo.session.add(
                    QuestionSkillORM(
                        id=f"{question_id}:{m.skill_slug}",
                        question_id=question_id,
                        skill_slug=m.skill_slug,
                        weight=m.weight,
                    )
                )
        await repo.session.commit()

        result = await skill_service.ingest_events(
            [_pass("u-skill", "test-two-sum", seq=1)]
        )
        assert result.accepted == 1

        states = await repo.get_states("u-skill")
        assert "hash-maps" in states
        assert states["hash-maps"].evidence_count == 1

    @pytest.mark.asyncio
    async def test_duplicate_event_skipped(self, skill_service):
        from app.models.orm import QuestionSkillORM

        repo = skill_service.repository
        repo.session.add(
            QuestionSkillORM(
                id="test-two-sum:hash-maps",
                question_id="test-two-sum",
                skill_slug="hash-maps",
                weight=0.6,
            )
        )
        await repo.session.commit()

        evt = _pass("u-skill", "test-two-sum", seq=2)
        await skill_service.ingest_events([evt, evt])
        states = await repo.get_states("u-skill")
        assert states["hash-maps"].evidence_count == 1

    @pytest.mark.asyncio
    async def test_graph_and_recommendations(self, skill_service):
        from app.models.orm import QuestionSkillORM

        repo = skill_service.repository
        for question_id, mappings in QUESTION_SKILLS.items():
            for m in mappings:
                repo.session.add(
                    QuestionSkillORM(
                        id=f"{question_id}:{m.skill_slug}",
                        question_id=question_id,
                        skill_slug=m.skill_slug,
                        weight=m.weight,
                    )
                )
        await repo.session.commit()

        for seq, q in enumerate(["test-two-sum", "test-reverse-string"]):
            await skill_service.ingest_events([_pass("u-skill", q, seq=seq)])

        graph = await skill_service.get_graph("u-skill")
        assert graph.skills
        assert any(s.skill_slug == "hash-maps" for s in graph.skills)
        assert graph.edges

        recs = await skill_service.get_recommendations("u-skill", limit=5)
        assert recs
        for rec in recs:
            assert rec.skill_slug
            assert rec.reason_text

    @pytest.mark.asyncio
    async def test_graph_status_derived_from_mastery_not_stale(self, skill_service):
        """Status must always be recomputed from mastery on read, even when no
        decay occurs and the stored status would be stale (e.g. NEW)."""
        from app.models.orm import QuestionSkillORM

        repo = skill_service.repository
        for question_id, mappings in QUESTION_SKILLS.items():
            for m in mappings:
                repo.session.add(
                    QuestionSkillORM(
                        id=f"{question_id}:{m.skill_slug}",
                        question_id=question_id,
                        skill_slug=m.skill_slug,
                        weight=m.weight,
                    )
                )
        await repo.session.commit()

        await skill_service.ingest_events([_pass("u-skill", "test-two-sum", seq=1)])
        graph = await skill_service.get_graph("u-skill")
        hash_maps = next(s for s in graph.skills if s.skill_slug == "hash-maps")
        # 0.3 mastery (1 distinct question, independent pass) must read as
        # learning, never as "new".
        assert hash_maps.mastery_score > 0.2
        assert hash_maps.status == SkillStatus.LEARNING
