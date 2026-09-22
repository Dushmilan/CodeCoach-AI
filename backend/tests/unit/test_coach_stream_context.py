"""Issue #264: streaming coach keeps learner/submission personalization."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.http_clients import reset_shared_clients


@pytest.mark.asyncio
async def test_stream_threads_personalization_into_prompt():
    """Learner context must reach the streamed prompt, not just the sync one."""
    from app.services.groq_service import GroqService

    reset_shared_clients()
    try:
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value = mock_instance

            class FakeResponse:
                status_code = 200
                headers = {}

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *exc):
                    return False

                async def aiter_lines(self):
                    yield 'data: {"choices": [{"delta": {"content": "hi"}}]}'

            captured = {}
            fake_response = FakeResponse()

            def fake_stream(*args, **kwargs):
                captured.update(kwargs.get("json", {}))
                return fake_response

            mock_instance.stream = MagicMock(side_effect=fake_stream)

            service = GroqService(api_key="gsk_test")
            seen_build_kwargs = {}
            real_build = service.prompts.build

            def spy_build(*args, **kwargs):
                seen_build_kwargs.update(kwargs)
                return real_build(*args, **kwargs)

            with patch.object(service.prompts, "build", side_effect=spy_build):
                chunks = [
                    chunk
                    async for chunk in service.stream(
                        problem="Two Sum",
                        code="x",
                        language="python",
                        message="hint?",
                        learner_context="## Learner Skill Context\n- arrays",
                        submission_context="## Recent Attempts\n- q1 failed",
                    )
                ]

            assert chunks, "expected streamed chunks"
            assert "arrays" in seen_build_kwargs.get("learner_context", "")
            assert "q1 failed" in seen_build_kwargs.get("submission_context", "")
    finally:
        reset_shared_clients()
