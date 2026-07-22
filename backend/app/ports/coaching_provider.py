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
    ) -> AsyncIterator[str]:
        """Yield streaming text chunks from the coaching backend."""
        ...  # pragma: no cover
