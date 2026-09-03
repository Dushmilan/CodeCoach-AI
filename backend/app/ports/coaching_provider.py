"""CoachingProvider — port for AI coaching interactions.

Defines the interface that coaching adapters (NIM, mock, etc.) must satisfy.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional


class CoachingProvider(ABC):
    """Port for AI coaching. Adapters implement this for different backends."""

    @abstractmethod
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
    ) -> Dict[str, Any]:
        """Return a structured coaching response as a dict."""
        ...

    @abstractmethod
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
        surface: str = "questions",
    ) -> AsyncIterator[str]:
        """Yield streaming text chunks from the coaching backend."""
        ...  # pragma: no cover

    async def get_animation_script(
        self,
        problem: str,
        code: str,
        language: str,
        difficulty: str = "medium",
        lesson_context: Optional[str] = None,
        initial_code: Optional[str] = None,
        question: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return a standalone visual algorithm animation script.

        Unlike get_structured this returns only the validated animation (no
        chat text) for the dedicated Animate viewer. Returns None when a
        valid animation could not be generated. Adapters that only support
        text coaching may leave this unimplemented.
        """
        raise NotImplementedError  # pragma: no cover
