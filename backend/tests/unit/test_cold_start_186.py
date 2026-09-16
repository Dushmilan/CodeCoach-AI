"""Cold-start fallback for fresh enrolled students (Issue #186)."""

import asyncio

import pytest

from app.models.schemas import Difficulty, Question
from app.services.skill_graph_rules import cold_start_order
from app.services.skill_graph_service import SkillGraphService
from app.services.skill_taxonomy import QUESTION_SKILLS, ROADMAP_ORDER

from tests.simulation.harness import build_seeded_repo


def _fake_question(question_id: str) -> Question:
    return Question(
        id=question_id,
        title=question_id.replace("-", " ").title(),
        difficulty=Difficulty.EASY,
        category="arrays",
        company_tags=[],
        description="Cold-start starter.",
        starter={"python": "def solve():\n    pass"},
        examples=[],
        test_cases=[],
    )


class TestColdStartOrder:
    def test_preserves_programme_order_dedupes_and_caps(self):
        ordered = cold_start_order(["q1", "q2", "q1", "q3", "missing"], limit=3)
        assert ordered == ["q1", "q2", "q3"]

    def test_deterministic(self):
        ids = ["b", "a", "c"]
        assert cold_start_order(ids, limit=5) == cold_start_order(ids, limit=5)


class TestMappingGapRegression:
    def test_tries_and_math_geometry_have_mappings(self):
        by_skill: dict[str, list[str]] = {}
        for qid, mappings in QUESTION_SKILLS.items():
            for m in mappings:
                by_skill.setdefault(m.skill_slug, []).append(qid)
        assert by_skill.get("tries"), "tries has zero mapped questions"
        assert by_skill.get("math-geometry"), "math-geometry has zero mappings"
        assert "tries" in ROADMAP_ORDER and "math-geometry" in ROADMAP_ORDER


class TestEnrolledFallback:
    def test_fresh_enrolled_student_gets_programme_starters(self):
        repo = build_seeded_repo()
        service = SkillGraphService(repository=repo)

        # Isolate the fallback: no skill-graph recs, no states.
        async def no_recs(*args, **kwargs):
            return []

        service.get_recommendations = no_recs  # type: ignore[method-assign]

        async def starters(uid, limit=5):
            return ["two-sum", "contains-duplicate"][:limit]

        service.get_enrolled_programme_starters = starters  # type: ignore[method-assign]

        async def loader(qid: str):
            if qid not in ("two-sum", "contains-duplicate"):
                return None
            return _fake_question(qid)

        async def run():
            return await service.get_recommended_questions(
                "fresh-enrolled", loader, limit=2
            )

        results = asyncio.run(run())
        assert [r.question.id for r in results] == ["two-sum", "contains-duplicate"]
        assert all(r.reason_text for r in results)


class TestEnrolledStartersSQL:
    @pytest.mark.asyncio
    async def test_programme_order_from_enrollments(self, test_db):
        import pytest_asyncio  # noqa: F401 (documents async fixture source)

        from app.models.orm import (
            ClassroomEnrollmentORM,
            ClassroomORM,
            CourseORM,
            LessonORM,
            ModuleORM,
            QuestionORM,
            UserORM,
        )
        from app.repositories.sql_skill_graph_repository import (
            SqlSkillGraphRepository,
        )

        session = test_db
        session.add(
            UserORM(
                id="fresh-186",
                username="fresh186",
                email="fresh186@test.com",
                hashed_password="hash",
            )
        )
        for qid in ("two-sum", "contains-duplicate"):
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
        session.add(
            CourseORM(
                id="course-186",
                title="Programme 186",
                description="seed",
                language="python",
                icon="code",
                order=1,
            )
        )
        session.add(
            ModuleORM(
                id="mod-186",
                course_id="course-186",
                title="M1",
                description="seed",
                order=1,
            )
        )
        session.add(
            LessonORM(
                id="les-186-1",
                course_id="course-186",
                module_id="mod-186",
                title="L1",
                type="exercise",
                content="seed",
                order=1,
                question_id="two-sum",
                language="python",
            )
        )
        session.add(
            LessonORM(
                id="les-186-2",
                course_id="course-186",
                module_id="mod-186",
                title="L2",
                type="exercise",
                content="seed",
                order=2,
                question_id="contains-duplicate",
                language="python",
            )
        )
        session.add(
            ClassroomORM(
                id="room-186",
                course_id="course-186",
                owner_id=None,
                name="Room 186",
                invite_code="INV186",
            )
        )
        session.add(
            ClassroomEnrollmentORM(
                id="enr-186",
                classroom_id="room-186",
                user_id="fresh-186",
                role="student",
            )
        )
        await session.commit()
        repo = SqlSkillGraphRepository(session)
        starters = await repo.get_enrolled_programme_starters("fresh-186", limit=5)
        assert starters == ["two-sum", "contains-duplicate"]
        assert await repo.get_enrolled_programme_starters("ghost-186") == []
