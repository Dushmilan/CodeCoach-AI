import pytest
import pytest_asyncio
from app.models.orm import UserORM, CourseORM
from app.models.course_schemas import CourseProgress


@pytest_asyncio.fixture
async def seeded_db(test_db):
    session = test_db
    session.add(
        UserORM(
            id="u-1",
            username="testuser",
            email="test@test.com",
            hashed_password="hash",
        )
    )
    session.add(
        CourseORM(
            id="c-1",
            title="Python",
            description="Learn Python",
            language="python",
            icon="python",
            order=1,
        )
    )
    await session.commit()
    return session


@pytest_asyncio.fixture
async def repo(seeded_db):
    from app.repositories.sql_progress_repository import SqlProgressRepository

    return SqlProgressRepository(seeded_db)


class TestSqlProgressRepository:
    @pytest.mark.asyncio
    async def test_get_progress_not_found(self, repo):
        progress = await repo.get_progress("u-1", "c-1")
        assert progress is None

    @pytest.mark.asyncio
    async def test_mark_lesson_complete_creates_progress(self, repo):
        progress = await repo.mark_lesson_complete("u-1", "c-1", "l-1")
        assert progress.user_id == "u-1"
        assert progress.course_id == "c-1"
        assert "l-1" in progress.completed_lessons
        assert len(progress.completed_lessons) == 1

    @pytest.mark.asyncio
    async def test_mark_lesson_complete_twice_no_duplicate(self, repo):
        await repo.mark_lesson_complete("u-1", "c-1", "l-1")
        progress = await repo.mark_lesson_complete("u-1", "c-1", "l-1")

        assert len(progress.completed_lessons) == 1

    @pytest.mark.asyncio
    async def test_mark_lesson_complete_multiple(self, repo):
        await repo.mark_lesson_complete("u-1", "c-1", "l-1")
        await repo.mark_lesson_complete("u-1", "c-1", "l-2")
        progress = await repo.mark_lesson_complete("u-1", "c-1", "l-3")

        assert len(progress.completed_lessons) == 3
        assert "l-1" in progress.completed_lessons
        assert "l-2" in progress.completed_lessons
        assert "l-3" in progress.completed_lessons

    @pytest.mark.asyncio
    async def test_get_all_progress(self, repo):
        await repo.mark_lesson_complete("u-1", "c-1", "l-1")

        all_progress = await repo.get_all_progress("u-1")
        assert len(all_progress) == 1
        assert all_progress[0].course_id == "c-1"

    @pytest.mark.asyncio
    async def test_get_all_progress_multiple_courses(self, repo):
        session = repo.session
        session.add(
            CourseORM(
                id="c-2",
                title="Java",
                description="Learn Java",
                language="java",
                icon="java",
                order=2,
            )
        )
        await session.commit()

        await repo.mark_lesson_complete("u-1", "c-1", "l-1")
        await repo.mark_lesson_complete("u-1", "c-2", "l-a")

        all_progress = await repo.get_all_progress("u-1")
        assert len(all_progress) == 2

    @pytest.mark.asyncio
    async def test_get_all_progress_empty(self, repo):
        all_progress = await repo.get_all_progress("u-1")
        assert all_progress == []

    @pytest.mark.asyncio
    async def test_save_progress(self, repo):
        progress = CourseProgress(
            user_id="u-1", course_id="c-1", completed_lessons=["l-1", "l-2"]
        )
        await repo.save(progress)

        fetched = await repo.get_progress("u-1", "c-1")
        assert fetched is not None
        assert len(fetched.completed_lessons) == 2

    @pytest.mark.asyncio
    async def test_save_updates_existing(self, repo):
        await repo.mark_lesson_complete("u-1", "c-1", "l-1")

        progress = await repo.get_progress("u-1", "c-1")
        progress.completed_lessons.append("l-2")
        await repo.save(progress)

        fetched = await repo.get_progress("u-1", "c-1")
        assert len(fetched.completed_lessons) == 2

    @pytest.mark.asyncio
    async def test_last_accessed_updates(self, repo):
        await repo.mark_lesson_complete("u-1", "c-1", "l-1")
        progress = await repo.mark_lesson_complete("u-1", "c-1", "l-2")

        assert progress.last_accessed_lesson_id == "l-2"
