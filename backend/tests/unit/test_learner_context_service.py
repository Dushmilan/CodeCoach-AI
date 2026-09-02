"""Unit tests for LearnerContextService — cache-aside, truncation, degraded paths."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.cache_keys import (
    COACH_CONTEXT_TTL,
    coach_context_key,
    recent_submissions_key,
    skill_graph_key,
)
from app.services.learner_context_service import (
    LearnerContextService,
    MAX_CODE_SNIPPET,
    MAX_ERROR_SIG,
    MAX_SKILLS_IN_BLOCK,
)


def _make_cache():
    m = AsyncMock()
    m.get = AsyncMock(return_value=None)
    m.set = AsyncMock(return_value=True)
    m.delete = AsyncMock(return_value=True)
    return m


def _skill(slug, mastery, status, trend="stable", recent=0, name=None):
    return {
        "skill_slug": slug,
        "name": name or slug,
        "mastery_score": mastery,
        "status": status,
        "trend": trend,
        "recent_error_count": recent,
    }


class TestLearnerContextService:
    @pytest.mark.asyncio
    async def test_empty_user_returns_empty(self):
        svc = LearnerContextService(
            cache=_make_cache(), skill_service=AsyncMock(), submission_repo=AsyncMock()
        )
        result = await svc.get_context("")
        assert result == {"skill_block": "", "submission_block": ""}

    @pytest.mark.asyncio
    async def test_cache_hit_returns_without_db(self):
        cache = _make_cache()
        cached = {"skill_block": "skill-hit", "submission_block": "sub-hit"}
        cache.get = AsyncMock(return_value=cached)
        skill_mock = AsyncMock()
        sub_mock = AsyncMock()
        svc = LearnerContextService(
            cache=cache, skill_service=skill_mock, submission_repo=sub_mock
        )
        result = await svc.get_context("u1")
        assert result == cached
        cache.get.assert_called_once_with(coach_context_key("u1"))
        skill_mock.get_graph.assert_not_called()
        sub_mock.list_by_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_builds_and_caches(self):
        cache = _make_cache()

        # first call miss for coach ctx, then miss for skill graph and submissions
        async def get_side_effect(key):
            if key == coach_context_key("u1"):
                return None
            if key == skill_graph_key("u1"):
                return None
            if key == recent_submissions_key("u1"):
                return None
            return None

        cache.get = AsyncMock(side_effect=get_side_effect)

        graph = MagicMock()
        graph.model_dump.return_value = {
            "skills": [
                _skill("arrays", 0.1, "learning"),
                _skill("hash-maps", 0.9, "strong"),
            ]
        }
        skill_svc = AsyncMock()
        skill_svc.get_graph = AsyncMock(return_value=graph)

        sub_repo = AsyncMock()
        sub_repo.list_by_user = AsyncMock(
            return_value=[
                {
                    "question_id": "q1",
                    "passed": True,
                    "code": "print('hi')",
                    "error_signature": "",
                }
            ]
        )

        svc = LearnerContextService(
            cache=cache, skill_service=skill_svc, submission_repo=sub_repo
        )
        result = await svc.get_context("u1")
        assert "arrays" in result["skill_block"]
        assert "Recent Attempts" in result["submission_block"]
        # should cache composed context + pieces
        assert cache.set.call_count >= 3  # skill_graph, submissions, coach context
        # check coach context cached with TTL
        coach_calls = [
            c for c in cache.set.call_args_list if c.args[0] == coach_context_key("u1")
        ]
        assert coach_calls
        assert (
            coach_calls[0].kwargs.get("ttl") == COACH_CONTEXT_TTL
            or coach_calls[0].args[2] == COACH_CONTEXT_TTL
        )

    @pytest.mark.asyncio
    async def test_skill_block_priority_and_limit(self):
        cache = _make_cache()
        cache.get = AsyncMock(
            side_effect=lambda k: None if k != coach_context_key("u2") else None
        )
        # 5 skills, only weakest priority should be picked up to MAX_SKILLS_IN_BLOCK=3
        skills = [
            _skill("s1", 0.05, "learning"),
            _skill("s2", 0.1, "developing"),
            _skill("s3", 0.2, "needs_review"),
            _skill("s4", 0.8, "strong"),
            _skill("s5", 0.9, "strong"),
        ]
        graph = MagicMock()
        graph.model_dump.return_value = {"skills": skills}
        skill_svc = AsyncMock()
        skill_svc.get_graph = AsyncMock(return_value=graph)
        svc = LearnerContextService(
            cache=cache, skill_service=skill_svc, submission_repo=AsyncMock()
        )
        block = await svc._get_skill_block("u2")
        # should contain the 3 weakest priority items, not the strong ones beyond limit
        assert "s1" in block
        assert "s2" in block
        assert "s3" in block
        assert block.count("\n-") == MAX_SKILLS_IN_BLOCK
        assert "s5" not in block

    @pytest.mark.asyncio
    async def test_submission_block_truncation_and_escaping(self):
        cache = _make_cache()
        cache.get = AsyncMock(return_value=None)
        long_code = "a" * 100 + "```evil" + "b" * (MAX_CODE_SNIPPET + 100)
        long_sig = "e" * (MAX_ERROR_SIG + 50)
        subs = [
            {
                "question_id": "q-long",
                "passed": False,
                "code": long_code,
                "error_signature": long_sig,
            },
            MagicMock(
                question_id="q-obj",
                passed=True,
                code="print('x')",
                error_signature=None,
            ),
        ]
        # MagicMock for second item needs getattr setup
        subs[1].__str__ = lambda _: "mock"
        repo = AsyncMock()
        repo.list_by_user = AsyncMock(return_value=subs)
        svc = LearnerContextService(
            cache=cache, skill_service=AsyncMock(), submission_repo=repo
        )
        block = await svc._get_submission_block("u3")
        assert "q-long" in block
        # code should be truncated and ``` escaped
        assert "```" not in block  # escaped to '''
        assert "'''" in block
        # error sig truncated
        assert "e" * MAX_ERROR_SIG in block
        assert "e" * (MAX_ERROR_SIG + 1) not in block

    @pytest.mark.asyncio
    async def test_degraded_on_skill_failure_still_returns_submission(self):
        cache = _make_cache()
        cache.get = AsyncMock(return_value=None)
        skill_svc = AsyncMock()
        skill_svc.get_graph = AsyncMock(side_effect=Exception("db down"))
        repo = AsyncMock()
        repo.list_by_user = AsyncMock(
            return_value=[
                {
                    "question_id": "q1",
                    "passed": True,
                    "code": "x",
                    "error_signature": "",
                }
            ]
        )
        svc = LearnerContextService(
            cache=cache, skill_service=skill_svc, submission_repo=repo
        )
        result = await svc.get_context("u-degraded")
        assert result["skill_block"] == ""
        assert "q1" in result["submission_block"]

    @pytest.mark.asyncio
    async def test_cache_get_failure_degraded(self):
        cache = AsyncMock()
        cache.get = AsyncMock(side_effect=Exception("redis down"))
        cache.set = AsyncMock(side_effect=Exception("redis down"))
        skill_svc = AsyncMock()
        skill_svc.get_graph = AsyncMock(side_effect=Exception("skip"))
        svc = LearnerContextService(
            cache=cache, skill_service=skill_svc, submission_repo=AsyncMock()
        )
        # should not raise, return empty blocks
        result = await svc.get_context("u-redis-down")
        assert result["skill_block"] == ""
        assert result["submission_block"] == ""

    @pytest.mark.asyncio
    async def test_invalidate_deletes_keys(self):
        cache = _make_cache()
        svc = LearnerContextService(
            cache=cache, skill_service=AsyncMock(), submission_repo=AsyncMock()
        )
        await svc.invalidate("u-inv")
        deleted = [c.args[0] for c in cache.delete.call_args_list]
        assert coach_context_key("u-inv") in deleted
        assert skill_graph_key("u-inv") in deleted
        assert recent_submissions_key("u-inv") in deleted
        assert any("codecoach:skills:recs:u-inv" in k for k in deleted)

    @pytest.mark.asyncio
    async def test_invalidate_no_cache_noop(self):
        svc = LearnerContextService(
            cache=None, skill_service=AsyncMock(), submission_repo=AsyncMock()
        )
        # should not raise
        await svc.invalidate("u-no-cache")
        await svc.invalidate("")

    @pytest.mark.asyncio
    async def test_skill_block_empty_when_no_skills(self):
        cache = _make_cache()
        cache.get = AsyncMock(return_value=None)
        graph = MagicMock()
        graph.model_dump.return_value = {"skills": []}
        skill_svc = AsyncMock()
        skill_svc.get_graph = AsyncMock(return_value=graph)
        svc = LearnerContextService(
            cache=cache, skill_service=skill_svc, submission_repo=AsyncMock()
        )
        block = await svc._get_skill_block("u-empty")
        assert block == ""

    @pytest.mark.asyncio
    async def test_submission_block_handles_pydantic_and_dict(self):
        cache = _make_cache()
        cache.get = AsyncMock(return_value=None)
        # Simulate pydantic object with model_dump
        pydantic_obj = MagicMock()
        pydantic_obj.model_dump.return_value = {
            "question_id": "q-pyd",
            "passed": True,
            "code": "code",
            "error_signature": "sig",
        }
        repo = AsyncMock()
        repo.list_by_user = AsyncMock(return_value=[pydantic_obj])
        svc = LearnerContextService(
            cache=cache, skill_service=AsyncMock(), submission_repo=repo
        )
        block = await svc._get_submission_block("u-pyd")
        assert "q-pyd" in block
