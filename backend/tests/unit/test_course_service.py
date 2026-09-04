import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.course_service import CourseService
from app.models.course_schemas import Course, Module, Lesson, CourseProgress, LessonType


@pytest.fixture
def mock_course_repo():
    repo = MagicMock()
    repo.get_all_courses = AsyncMock(return_value=[])
    repo.get_course_by_id = AsyncMock(return_value=None)
    repo.get_module_by_id = AsyncMock(return_value=None)
    repo.get_lesson_by_id = AsyncMock(return_value=None)
    repo.get_modules_by_course = AsyncMock(return_value=[])
    repo.get_modules_by_course_batch = AsyncMock(return_value=[])
    repo.get_lessons_by_module = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_progress_repo():
    repo = MagicMock()
    repo.get_progress = AsyncMock(return_value=None)
    repo.get_all_progress = AsyncMock(return_value=[])
    repo.mark_lesson_complete = AsyncMock()
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def sample_course():
    return Course(
        id="python-fundamentals",
        title="Python Fundamentals",
        description="Learn Python from scratch",
        language="python",
        icon="python",
        order=1,
        modules=["python-intro"],
    )


@pytest.fixture
def sample_module():
    return Module(
        id="python-intro",
        course_id="python-fundamentals",
        title="Getting Started",
        description="Variables, data types, and basic I/O",
        order=1,
        lessons=["py-hello-world"],
    )


@pytest.fixture
def sample_lesson():
    return Lesson(
        id="py-hello-world",
        course_id="python-fundamentals",
        module_id="python-intro",
        title="Hello, World!",
        type=LessonType.THEORY,
        content="# Hello, World!\n\nPrint to the console.",
        order=1,
        language="python",
    )


class TestCourseService:
    @pytest.mark.asyncio
    async def test_list_courses_empty(self, mock_course_repo, mock_progress_repo):
        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.list_courses()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_courses_with_progress(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        mock_course_repo.get_all_courses = AsyncMock(return_value=[sample_course])
        mock_module = MagicMock()
        mock_module.id = "python-intro"
        mock_module.lessons = ["py-hello-world"]
        mock_course_repo.get_modules_by_course_batch = AsyncMock(
            return_value=[mock_module]
        )
        mock_progress_repo.get_progress = AsyncMock(
            return_value=CourseProgress(
                user_id="user1",
                course_id="python-fundamentals",
                completed_lessons=["py-hello-world"],
            )
        )

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.list_courses(user_id="user1")

        assert len(result) == 1
        assert result[0].progress == 100.0

    @pytest.mark.asyncio
    async def test_list_courses_unauthenticated(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        mock_course_repo.get_all_courses = AsyncMock(return_value=[sample_course])

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.list_courses(user_id=None)

        assert len(result) == 1
        assert result[0].progress == 0.0

    @pytest.mark.asyncio
    async def test_get_course_by_id(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        mock_course_repo.get_course_by_id = AsyncMock(return_value=sample_course)

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.get_course("python-fundamentals")

        assert result is not None
        assert result.id == "python-fundamentals"

    @pytest.mark.asyncio
    async def test_get_course_not_found(self, mock_course_repo, mock_progress_repo):
        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.get_course("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_course_with_modules(
        self, mock_course_repo, mock_progress_repo, sample_course, sample_module
    ):
        mock_course_repo.get_course_by_id = AsyncMock(return_value=sample_course)
        mock_course_repo.get_modules_by_course = AsyncMock(return_value=[sample_module])
        mock_course_repo.get_lessons_by_module = AsyncMock(
            return_value=[
                Lesson(
                    id="py-hello-world",
                    course_id="python-fundamentals",
                    module_id="python-intro",
                    title="Hello, World!",
                    type=LessonType.THEORY,
                    content="# Hello, World!",
                    order=1,
                    language="python",
                )
            ]
        )

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.get_course_with_modules("python-fundamentals")

        assert result is not None
        assert len(result["modules"]) == 1
        assert len(result["modules"][0]["lessons"]) == 1

    @pytest.mark.asyncio
    async def test_get_lesson(
        self, mock_course_repo, mock_progress_repo, sample_lesson
    ):
        mock_course_repo.get_lesson_by_id = AsyncMock(return_value=sample_lesson)

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.get_lesson("py-hello-world")

        assert result is not None
        assert result.id == "py-hello-world"

    @pytest.mark.asyncio
    async def test_get_lesson_not_found(self, mock_course_repo, mock_progress_repo):
        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.get_lesson("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_mark_lesson_complete(self, mock_course_repo, mock_progress_repo):
        expected = CourseProgress(
            user_id="user1",
            course_id="python-fundamentals",
            completed_lessons=["py-hello-world"],
        )
        mock_progress_repo.mark_lesson_complete = AsyncMock(return_value=expected)

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.mark_lesson_complete(
            "user1", "python-fundamentals", "py-hello-world"
        )

        assert result is not None
        assert "py-hello-world" in result.completed_lessons

    @pytest.mark.asyncio
    async def test_get_progress(self, mock_course_repo, mock_progress_repo):
        expected = CourseProgress(
            user_id="user1",
            course_id="python-fundamentals",
            completed_lessons=["py-hello-world"],
        )
        mock_progress_repo.get_progress = AsyncMock(return_value=expected)

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.get_progress("user1", "python-fundamentals")

        assert result is not None
        assert len(result.completed_lessons) == 1

    @pytest.mark.asyncio
    async def test_get_all_progress(self, mock_course_repo, mock_progress_repo):
        expected = [
            CourseProgress(
                user_id="user1",
                course_id="python-fundamentals",
                completed_lessons=["py-hello-world"],
            ),
            CourseProgress(
                user_id="user1",
                course_id="c-programming",
                completed_lessons=[],
            ),
        ]
        mock_progress_repo.get_all_progress = AsyncMock(return_value=expected)

        service = CourseService(
            course_repo=mock_course_repo, progress_repo=mock_progress_repo
        )
        result = await service.get_all_progress("user1")

        assert len(result) == 2


class _FakeListCache:
    """In-memory async stand-in for RedisCache (get/set/SET NX/delete)."""

    def __init__(self):
        self.store = {}
        self.set_ttls = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ttl=300):
        self.set_ttls[key] = ttl
        self.store[key] = value

    async def set_if_absent(self, key, value, ttl=300):
        if key in self.store:
            return False
        self.store[key] = value
        return True

    async def delete(self, pattern):
        if pattern in self.store:
            del self.store[pattern]
            return 1
        return 0


class _NeverAvailableCache(_FakeListCache):
    """Simulates a stuck lock holder: lock never acquired, value never lands."""

    async def get(self, key):
        return None

    async def set_if_absent(self, key, value, ttl=300):
        return False


class TestAnonymousCourseListCache:
    @pytest.mark.asyncio
    async def test_anonymous_list_served_from_cache(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        mock_course_repo.get_all_courses = AsyncMock(return_value=[sample_course])
        cache = _FakeListCache()

        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            list_ttl=30,
        )
        first = await service.list_courses(user_id=None)
        second = await service.list_courses(user_id=None)

        assert mock_course_repo.get_all_courses.call_count == 1
        assert (
            [c.id for c in second] == [c.id for c in first] == ["python-fundamentals"]
        )

    @pytest.mark.asyncio
    async def test_cache_entry_uses_configured_ttl(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        mock_course_repo.get_all_courses = AsyncMock(return_value=[sample_course])
        cache = _FakeListCache()

        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            list_ttl=7,
        )
        await service.list_courses(user_id=None)

        assert 7 in cache.set_ttls.values()

    @pytest.mark.asyncio
    async def test_concurrent_miss_builds_only_once(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        import asyncio

        async def slow_repo():
            await asyncio.sleep(0.05)
            return [sample_course]

        mock_course_repo.get_all_courses = AsyncMock(side_effect=slow_repo)
        cache = _FakeListCache()
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            list_ttl=30,
        )

        results = await asyncio.gather(
            service.list_courses(user_id=None),
            service.list_courses(user_id=None),
        )

        assert mock_course_repo.get_all_courses.call_count == 1
        assert [c.id for c in results[0]] == ["python-fundamentals"]
        assert [c.id for c in results[1]] == ["python-fundamentals"]

    @pytest.mark.asyncio
    async def test_stuck_lock_falls_back_to_direct_build(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        mock_course_repo.get_all_courses = AsyncMock(return_value=[sample_course])

        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=_NeverAvailableCache(),
            list_ttl=30,
        )
        result = await service.list_courses(user_id=None)

        assert mock_course_repo.get_all_courses.call_count == 1
        assert [c.id for c in result] == ["python-fundamentals"]

    @pytest.mark.asyncio
    async def test_authenticated_list_bypasses_cache(
        self, mock_course_repo, mock_progress_repo, sample_course
    ):
        mock_course_repo.get_all_courses = AsyncMock(return_value=[sample_course])
        cache = _FakeListCache()

        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            list_ttl=30,
        )
        await service.list_courses(user_id="user1")
        await service.list_courses(user_id="user1")

        assert mock_course_repo.get_all_courses.call_count == 2
        assert cache.store == {}
