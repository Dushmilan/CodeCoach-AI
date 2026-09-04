"""Stateful coaching adapter — sent -> completed/failed persistence.

Wraps a CoachingProvider (e.g. GroqService) with durable intent rows via
CoachingInteractionRepository. Persistence is best-effort: DB failures are
logged and never break the coaching response (degrade open).
"""

import hashlib
import logging
import uuid
from typing import Any, AsyncIterator, Optional

from app.ports.coaching_provider import CoachingProvider
from app.ports.coaching_interaction_repository import CoachingInteractionRepository

logger = logging.getLogger(__name__)


def hash_content(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:64]


class CoachingAdapter(CoachingProvider):
    """CoachingProvider with Supabase-backed state transitions."""

    def __init__(
        self,
        inner: CoachingProvider,
        repo: Optional[CoachingInteractionRepository] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.inner = inner
        self.repo = repo
        self.user_id = user_id
        self.request_id = request_id or uuid.uuid4().hex

    async def get_structured(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        chat_history: Optional[list] = None,
        initial_code: Optional[str] = None,
        learner_context: Optional[str] = None,
        submission_context: Optional[str] = None,
        surface: str = "questions",
    ) -> dict[str, Any]:
        interaction = None
        if self.repo is not None and self.user_id:
            try:
                interaction = await self.repo.create_sent(
                    user_id=self.user_id,
                    question_id=None,
                    mode=mode,
                    language=language,
                    problem_hash=hash_content(problem),
                    code_hash=hash_content(code),
                    idempotency_key=uuid.uuid4().hex,
                    request_payload={
                        "mode": mode,
                        "language": language,
                        "difficulty": difficulty,
                    },
                    request_id=self.request_id,
                )
            except Exception:  # noqa: BLE001 - persistence must not break coaching
                logger.warning("Failed to persist coaching sent state", exc_info=True)
                interaction = None
        try:
            result = await self.inner.get_structured(
                problem=problem,
                code=code,
                language=language,
                message=message,
                mode=mode,
                difficulty=difficulty,
                lesson_context=lesson_context,
                chat_history=chat_history,
                initial_code=initial_code,
                learner_context=learner_context,
                submission_context=submission_context,
                surface=surface,
            )
        except Exception as exc:  # noqa: BLE001 - map to failed state then re-raise
            if interaction is not None and self.repo is not None:
                try:
                    status = "timeout" if "timeout" in str(exc).lower() else "failed"
                    await self.repo.mark_failed(
                        interaction.id,
                        status=status,
                        error_code=type(exc).__name__[:50],
                        error_message=str(exc)[:2000],
                    )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Failed to persist coaching failed state", exc_info=True
                    )
            raise
        if interaction is not None and self.repo is not None:
            try:
                await self.repo.mark_completed(interaction.id, response_payload=result)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "Failed to persist coaching completed state", exc_info=True
                )
        return result

    async def stream(
        self,
        problem: str,
        code: str,
        language: str,
        message: str,
        mode: str = "hint",
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        chat_history: Optional[list] = None,
        initial_code: Optional[str] = None,
    ) -> AsyncIterator[str]:
        async for chunk in self.inner.stream(
            problem=problem,
            code=code,
            language=language,
            message=message,
            mode=mode,
            difficulty=difficulty,
            lesson_context=lesson_context,
            chat_history=chat_history,
            initial_code=initial_code,
        ):
            yield chunk

    async def get_animation_script(
        self,
        problem: str,
        code: str,
        language: str,
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        initial_code: Optional[str] = None,
        question: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        return await self.inner.get_animation_script(
            problem=problem,
            code=code,
            language=language,
            difficulty=difficulty,
            lesson_context=lesson_context,
            initial_code=initial_code,
            question=question,
        )
