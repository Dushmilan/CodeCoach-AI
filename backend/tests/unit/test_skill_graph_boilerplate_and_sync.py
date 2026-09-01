"""TDD red tests for boilerplate graph + DB sync (submissions -> skill graph).

These must fail before implementation and pass after.
"""

import pytest
import pytest_asyncio

from app.models.orm import QuestionORM, SkillORM, UserORM
from app.models.skill_graph_schemas import SkillStatus
from app.models.submission_schemas import SubmissionIn
from app.repositories.sql_skill_graph_repository import SqlSkillGraphRepository
from app.repositories.sql_submission_repository import SqlSubmissionRepository
from app.services.skill_graph_service import SkillGraphService
from app.services.skill_taxonomy import SKILLS, QUESTION_SKILLS


@pytest_asyncio.fixture
async def seeded_db(test_db):
    session = test_db
    # users
    session.add(
        UserORM(
            id="u-sync",
            username="syncuser",
            email="syncuser@test.com",
            hashed_password="hash",
        )
    )
    session.add(
        UserORM(
            id="u-boiler",
            username="boileruser",
            email="boileruser@test.com",
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
    # seed question_skills
    from app.models.orm import QuestionSkillORM

    for question_id, mappings in QUESTION_SKILLS.items():
        for m in mappings:
            session.add(
                QuestionSkillORM(
                    id=f"{question_id}:{m.skill_slug}",
                    question_id=question_id,
                    skill_slug=m.skill_slug,
                    weight=m.weight,
                )
            )
    await session.commit()
    return session


@pytest.mark.asyncio
async def test_boilerplate_true_returns_all_skills_for_new_user(seeded_db):
    repo = SqlSkillGraphRepository(seeded_db)
    svc = SkillGraphService(repository=repo)
    # new user has no states
    graph = await svc.get_graph("u-boiler", include_boilerplate=True)
    assert len(graph.skills) == len(SKILLS), (
        "boilerplate must return every taxonomy skill"
    )
    assert graph.edges  # edges always present
    for s in graph.skills:
        assert s.mastery_score == 0.0
        assert s.confidence == 0.0
        assert s.status == SkillStatus.NEW
        assert s.evidence_count == 0
        assert s.trend.value == "stable"


@pytest.mark.asyncio
async def test_boilerplate_false_still_empty_for_new_user(seeded_db):
    repo = SqlSkillGraphRepository(seeded_db)
    svc = SkillGraphService(repository=repo)
    graph = await svc.get_graph("u-boiler", include_boilerplate=False)
    assert graph.skills == []


@pytest.mark.asyncio
async def test_sync_from_submissions_builds_graph_via_db_query(seeded_db):
    skill_repo = SqlSkillGraphRepository(seeded_db)
    sub_repo = SqlSubmissionRepository(seeded_db)
    svc = SkillGraphService(repository=skill_repo)

    # Simulate already-completed questions in submissions table (no learning_events yet)
    await sub_repo.add(
        user_id="u-sync",
        submission=SubmissionIn(
            question_id="two-sum", code="x", language="python", passed=True
        ),
    )
    await sub_repo.add(
        user_id="u-sync",
        submission=SubmissionIn(
            question_id="contains-duplicate", code="x", language="python", passed=True
        ),
    )

    subs = await sub_repo.list_by_user("u-sync", limit=100)
    # This method does not exist yet — should be implemented
    result = await svc.sync_from_submissions("u-sync", subs)
    assert result.accepted >= 2

    graph = await svc.get_graph("u-sync")
    slugs = {s.skill_slug for s in graph.skills}
    # two-sum touches arrays+hash-maps, contains-duplicate touches hash-maps+arrays
    assert "hash-maps" in slugs
    assert "arrays" in slugs
    # idempotency: second sync must not double-count
    result2 = await svc.sync_from_submissions("u-sync", subs)
    assert result2.duplicate >= 2
    assert result2.accepted == 0


@pytest.mark.asyncio
async def test_sync_failed_submission_creates_failed_event(seeded_db):
    skill_repo = SqlSkillGraphRepository(seeded_db)
    sub_repo = SqlSubmissionRepository(seeded_db)
    svc = SkillGraphService(repository=skill_repo)
    await sub_repo.add(
        user_id="u-sync",
        submission=SubmissionIn(
            question_id="two-sum",
            code="bad",
            language="python",
            passed=False,
            error_signature="expected true got false",
        ),
    )
    subs = await sub_repo.list_by_user("u-sync", limit=100)
    passed_subs = [s for s in subs if s.question_id == "two-sum" and not s.passed]
    # need at least one failed
    assert passed_subs
    # sync only that failed one via fresh service with clean state
    # reset states first
    await skill_repo.delete_user_history("u-sync")
    # re-add clean failed
    # Use the single failed sub
    result = await svc.sync_from_submissions("u-sync", passed_subs)
    assert result.accepted == 1
    states = await skill_repo.get_states("u-sync")
    assert states["hash-maps"].recent_error_count == 1
