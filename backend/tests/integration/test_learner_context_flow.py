"""Integration: submit → skill graph → coach learner context with cache invalidation.

Lightweight version: verifies wiring via dependency overrides and mocks, avoids
heavy Supabase schema drops that stall the suite on the pooler.
"""

import pytest
from contextlib import contextmanager
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.api.coach import get_coaching_provider
from app.api.dependencies import get_learner_context_service_dependency


captured = {}


class CapturingProvider:
    async def get_structured(
        self,
        problem,
        code,
        language,
        message,
        mode="hint",
        difficulty="medium",
        lesson_context=None,
        chat_history=None,
        initial_code=None,
        learner_context=None,
        submission_context=None,
        surface="questions",
        **kwargs,
    ):
        captured["learner_context"] = learner_context
        captured["submission_context"] = submission_context
        captured["surface"] = surface
        return {
            "summary": "captured",
            "hints": [],
            "code_review": None,
            "complexity_analysis": None,
            "suggestions": [],
            "edge_cases": [],
            "explanation": None,
            "debug_help": None,
        }

    async def get_animation_script(self, *args, **kwargs):
        from tests.fixtures.mock_coaching_provider import LINEAR_SEARCH_ANIMATION

        return LINEAR_SEARCH_ANIMATION

    async def stream(self, *args, **kwargs):
        yield "captured"


@contextmanager
def mock_auth(user_id="test-learner", username="learner", plan="premium"):
    from app.api.auth_deps import get_current_user

    async def override():
        from app.models.auth_schemas import UserResponse

        return UserResponse(
            id=user_id,
            username=username,
            email="test@example.com",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
            plan=plan,
        )

    app.dependency_overrides[get_current_user] = override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def _override_provider():
    captured.clear()
    app.dependency_overrides[get_coaching_provider] = lambda: CapturingProvider()
    yield
    app.dependency_overrides.pop(get_coaching_provider, None)


@pytest.mark.usefixtures("test_env_vars")
class TestLearnerContextFlow:
    def test_submit_invalid_language_422(self, test_client: TestClient):
        with mock_auth():
            resp = test_client.post(
                "/api/submit/",
                json={
                    "question_id": "two-sum",
                    "code": "x",
                    "language": "invalid_lang",
                    "passed": True,
                },
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_coach_uses_cached_learner_context(self, async_client):
        """Coach endpoint should call learner_context_service and forward to provider."""
        from app.services.learner_context_service import LearnerContextService

        mock_svc = AsyncMock(spec=LearnerContextService)
        mock_svc.get_context = AsyncMock(
            return_value={"skill_block": "skill-ctx", "submission_block": "sub-ctx"}
        )
        mock_svc.invalidate = AsyncMock()

        app.dependency_overrides[get_learner_context_service_dependency] = lambda: (
            mock_svc
        )
        try:
            with mock_auth():
                resp = await async_client.post(
                    "/api/coach/",
                    json={
                        "problem": "p",
                        "code": "c",
                        "language": "python",
                        "message": "m",
                        "mode": "hint",
                        "difficulty": "easy",
                    },
                )
            assert resp.status_code == 200
            mock_svc.get_context.assert_called_once()
            # coach.py splits dict into two string kwargs
            assert captured.get("learner_context") == "skill-ctx"
            assert captured.get("submission_context") == "sub-ctx"
        finally:
            app.dependency_overrides.pop(get_learner_context_service_dependency, None)

    @pytest.mark.asyncio
    async def test_coach_learn_surface_skips_learner_context(self, async_client):
        """Learn surface must not fetch the skill graph and must forward surface."""
        from app.services.learner_context_service import LearnerContextService

        mock_svc = AsyncMock(spec=LearnerContextService)
        mock_svc.get_context = AsyncMock(
            return_value={"skill_block": "skill-ctx", "submission_block": "sub-ctx"}
        )
        mock_svc.invalidate = AsyncMock()

        app.dependency_overrides[get_learner_context_service_dependency] = lambda: (
            mock_svc
        )
        try:
            with mock_auth():
                resp = await async_client.post(
                    "/api/coach/",
                    json={
                        "problem": "Loops",
                        "code": "c",
                        "language": "python",
                        "message": "what is a loop?",
                        "mode": "explain",
                        "difficulty": "easy",
                        "lesson_context": "Loops 101",
                        "surface": "learn",
                    },
                )
            assert resp.status_code == 200
            mock_svc.get_context.assert_not_called()
            assert captured.get("surface") == "learn"
            assert captured.get("learner_context") in (None, "")
            assert captured.get("submission_context") in (None, "")
            assert resp.headers.get("X-Surface") == "learn"
        finally:
            app.dependency_overrides.pop(get_learner_context_service_dependency, None)

    @pytest.mark.asyncio
    async def test_coach_learn_requires_lesson_context(self, async_client):
        """Learn surface without lesson_context must 422, never reaching the provider."""
        with mock_auth():
            resp = await async_client.post(
                "/api/coach/",
                json={
                    "problem": "Loops",
                    "code": "c",
                    "language": "python",
                    "message": "what is a loop?",
                    "mode": "explain",
                    "difficulty": "easy",
                    "surface": "learn",
                },
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_coach_degraded_when_learner_context_fails(self, async_client):
        """Coach should still succeed if learner context throws (degraded)."""
        from app.services.learner_context_service import LearnerContextService

        mock_svc = AsyncMock(spec=LearnerContextService)
        mock_svc.get_context = AsyncMock(side_effect=Exception("redis down"))
        mock_svc.invalidate = AsyncMock()

        app.dependency_overrides[get_learner_context_service_dependency] = lambda: (
            mock_svc
        )
        try:
            with mock_auth():
                resp = await async_client.post(
                    "/api/coach/",
                    json={
                        "problem": "p",
                        "code": "c",
                        "language": "python",
                        "message": "m",
                        "mode": "hint",
                        "difficulty": "easy",
                    },
                )
            # coach should still return 200 with empty context fallback (implementation logs debug)
            # Current implementation does not catch exception inside coach.py, so we assert it does not 500
            # If it raises, this test will fail and we need to fix coach.py to degrade.
            assert resp.status_code in (200, 500)
            if resp.status_code == 500:
                pytest.fail(
                    "Coach did not degrade on learner_context failure — should return 200"
                )
        finally:
            app.dependency_overrides.pop(get_learner_context_service_dependency, None)

    @pytest.mark.asyncio
    async def test_submit_emits_event_and_invalidates(self, async_client):
        """Submit endpoint should persist, emit skill event, and invalidate cache via Redis."""
        from app.api.dependencies import (
            get_question_repo,
            get_executor,
            get_redis_cache,
            get_submission_repo,
            get_skill_graph_service_dependency,
        )
        from app.models.schemas import (
            Question,
            Difficulty,
            StarterCode,
            Example,
            TestCase,
        )
        from app.services.redis_service import RedisCache

        class MockRepo:
            async def get_by_id(self, qid):
                return Question(
                    id="two-sum",
                    title="Two Sum",
                    difficulty=Difficulty.EASY,
                    category="arrays",
                    description="d",
                    starter=StarterCode(python="def f(): pass"),
                    examples=[Example(input="1", output="1")],
                    test_cases=[TestCase(input="1", expected_output="1", hidden=False)],
                )

        class MockExec:
            async def execute(self, *a, **kw):
                from app.ports.code_executor import ExecutionResult

                return ExecutionResult(stdout="1\n", exit_code=0)

            async def evaluate_suite(self, language, code, test_cases):
                from app.ports.code_executor import TestCaseResult

                return [
                    TestCaseResult(
                        index=1,
                        passed=True,
                        input="1",
                        expected="1",
                        actual="1",
                        hidden=False,
                    )
                ]

        # Mock cache that records deletes
        mock_cache = AsyncMock(spec=RedisCache)
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)
        mock_cache.delete = AsyncMock(return_value=True)

        # Mock submission repo to avoid DB FK, and skill service to avoid DB
        mock_sub_repo = AsyncMock()
        mock_sub_repo.add = AsyncMock(
            return_value=MagicMock(id="sub-123", created_at=None)
        )
        mock_skill = AsyncMock()
        mock_skill.ingest_events = AsyncMock(return_value=MagicMock(accepted=1))

        app.dependency_overrides[get_question_repo] = lambda: MockRepo()
        app.dependency_overrides[get_executor] = lambda: MockExec()
        app.dependency_overrides[get_redis_cache] = lambda: mock_cache
        app.dependency_overrides[get_submission_repo] = lambda: mock_sub_repo
        app.dependency_overrides[get_skill_graph_service_dependency] = lambda: (
            mock_skill
        )

        try:
            with mock_auth():
                resp = await async_client.post(
                    "/api/submit/",
                    json={
                        "question_id": "two-sum",
                        "code": "print(1)",
                        "language": "python",
                    },
                )
            assert resp.status_code == 200
            # Invalidate should have deleted coach:ctx keys via mock_cache
            assert mock_cache.delete.called
            deleted = [c.args[0] for c in mock_cache.delete.call_args_list]
            assert any("coach:ctx" in k for k in deleted)
            assert mock_skill.ingest_events.called
        finally:
            for k in [
                get_question_repo,
                get_executor,
                get_redis_cache,
                get_submission_repo,
                get_skill_graph_service_dependency,
            ]:
                app.dependency_overrides.pop(k, None)
