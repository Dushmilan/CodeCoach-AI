"""Unit tests for the cached single-fetch learn summary (issue #268).

Learn page (logged-in) must return minimal per-course summaries from ONE
cached fetch: exactly two repo calls on a miss (courses + batched
progress), zero on a hit, explicit invalidation on progress writes, and a
catalog-version bump that retires stale entries despite the hour-long TTL.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.course_service import CourseService
from app.models.course_schemas import Course, CourseProgress


@pytest.fixture
def mock_course_repo():
    repo = MagicMock()
    repo.get_all_courses = AsyncMock(return_value=[])
    repo.get_modules_by_course_batch = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_progress_repo():
    repo = MagicMock()
    repo.get_progress = AsyncMock(return_value=None)
    repo.get_all_progress = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def two_courses():
    return [
        Course(
            id="python-fundamentals",
            title="Python Fundamentals",
            description="Learn Python",
            language="python",
            icon="python",
            order=1,
            modules=["mod-py"],
        ),
        Course(
            id="c-programming",
            title="C Programming",
            description="Learn C",
            language="c",
            icon="c",
            order=2,
            modules=["mod-c"],
        ),
    ]


def _module(mod_id, lessons):
    mod = MagicMock()
    mod.id = mod_id
    mod.lessons = lessons
    return mod


class _FakeLearnCache:
    """In-memory async stand-in for RedisCache (get/set/delete/incr)."""

    def __init__(self, fail=False):
        self.store = {}
        self.set_ttls = {}
        self.fail = fail

    async def get(self, key):
        if self.fail:
            raise ConnectionError("redis down")
        return self.store.get(key)

    async def set(self, key, value, ttl=300):
        if self.fail:
            raise ConnectionError("redis down")
        self.set_ttls[key] = ttl
        self.store[key] = value

    async def delete(self, key):
        if self.fail:
            raise ConnectionError("redis down")
        if key in self.store:
            del self.store[key]
            return 1
        return 0


def _repos_with_data(mock_course_repo, mock_progress_repo, two_courses):
    mock_course_repo.get_all_courses = AsyncMock(return_value=two_courses)
    mock_course_repo.get_modules_by_course_batch = AsyncMock(
        return_value=[_module("mod-py", ["l1", "l2"]), _module("mod-c", ["l3"])]
    )
    mock_progress_repo.get_all_progress = AsyncMock(
        return_value=[
            CourseProgress(
                user_id="user1",
                course_id="python-fundamentals",
                completed_lessons=["l1"],
                last_accessed_lesson_id="l1",
            )
        ]
    )


class TestLearnSummaryMiss:
    @pytest.mark.asyncio
    async def test_miss_returns_minimal_shape_with_single_progress_query(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        _repos_with_data(mock_course_repo, mock_progress_repo, two_courses)
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=_FakeLearnCache(),
            learn_ttl=3600,
        )

        result = await service.list_learn_summaries(user_id="user1")

        assert mock_course_repo.get_all_courses.call_count == 1
        assert mock_progress_repo.get_all_progress.call_count == 1
        assert mock_progress_repo.get_progress.call_count == 0
        assert [(s.id, s.title, s.language) for s in result] == [
            ("python-fundamentals", "Python Fundamentals", "python"),
            ("c-programming", "C Programming", "c"),
        ]
        assert [s.progress for s in result] == [50.0, 0.0]
        assert result[0].completed_lessons_count == 1
        assert result[0].last_accessed_lesson_id == "l1"
        assert result[1].completed_lessons_count == 0
        assert result[1].last_accessed_lesson_id is None
        # Minimal shape: no heavy catalog fields.
        assert set(result[0].model_dump()) == {
            "id",
            "title",
            "description",
            "language",
            "progress",
            "completed_lessons_count",
            "last_accessed_lesson_id",
        }

    @pytest.mark.asyncio
    async def test_anonymous_learn_has_zero_progress(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        mock_course_repo.get_all_courses = AsyncMock(return_value=two_courses)
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=_FakeLearnCache(),
            learn_ttl=3600,
        )

        result = await service.list_learn_summaries(user_id=None)

        assert [s.progress for s in result] == [0.0, 0.0]
        assert mock_progress_repo.get_all_progress.call_count == 0


class TestLearnSummaryCache:
    @pytest.mark.asyncio
    async def test_hit_serves_from_cache_without_repo_calls(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        _repos_with_data(mock_course_repo, mock_progress_repo, two_courses)
        cache = _FakeLearnCache()
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            learn_ttl=3600,
        )

        first = await service.list_learn_summaries(user_id="user1")
        second = await service.list_learn_summaries(user_id="user1")

        assert mock_course_repo.get_all_courses.call_count == 1
        assert mock_progress_repo.get_all_progress.call_count == 1
        assert [s.id for s in second] == [s.id for s in first]

    @pytest.mark.asyncio
    async def test_entry_uses_configured_learn_ttl(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        _repos_with_data(mock_course_repo, mock_progress_repo, two_courses)
        cache = _FakeLearnCache()
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            learn_ttl=3600,
        )

        await service.list_learn_summaries(user_id="user1")

        assert 3600 in cache.set_ttls.values()

    @pytest.mark.asyncio
    async def test_per_user_keys_do_not_leak_across_users(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        _repos_with_data(mock_course_repo, mock_progress_repo, two_courses)
        cache = _FakeLearnCache()
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            learn_ttl=3600,
        )

        await service.list_learn_summaries(user_id="user1")
        await service.list_learn_summaries(user_id="user2")

        assert mock_course_repo.get_all_courses.call_count == 2
        user_keys = [k for k in cache.store if "user1" in k]
        assert len(user_keys) == 1
        assert not any("user2" in k for k in user_keys)

    @pytest.mark.asyncio
    async def test_progress_write_invalidation_forces_rebuild(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        _repos_with_data(mock_course_repo, mock_progress_repo, two_courses)
        cache = _FakeLearnCache()
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            learn_ttl=3600,
        )

        await service.list_learn_summaries(user_id="user1")
        await service.invalidate_learn_cache(user_id="user1")
        await service.list_learn_summaries(user_id="user1")

        assert mock_course_repo.get_all_courses.call_count == 2

    @pytest.mark.asyncio
    async def test_catalog_bump_retires_stale_entries(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        _repos_with_data(mock_course_repo, mock_progress_repo, two_courses)
        cache = _FakeLearnCache()
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=cache,
            learn_ttl=3600,
        )

        await service.list_learn_summaries(user_id="user1")
        await service.bump_learn_catalog_version()
        await service.list_learn_summaries(user_id="user1")

        assert mock_course_repo.get_all_courses.call_count == 2

    @pytest.mark.asyncio
    async def test_redis_failure_falls_back_to_direct_build(
        self, mock_course_repo, mock_progress_repo, two_courses
    ):
        _repos_with_data(mock_course_repo, mock_progress_repo, two_courses)
        service = CourseService(
            course_repo=mock_course_repo,
            progress_repo=mock_progress_repo,
            cache=_FakeLearnCache(fail=True),
            learn_ttl=3600,
        )

        result = await service.list_learn_summaries(user_id="user1")

        assert [s.id for s in result] == ["python-fundamentals", "c-programming"]
        assert result[0].progress == 50.0
