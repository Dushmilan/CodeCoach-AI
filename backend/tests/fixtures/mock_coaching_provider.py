"""Mock coaching provider for tests."""

from typing import AsyncIterator, Dict, Any, Optional

from app.ports.coaching_provider import CoachingProvider


class MockCoachingProvider(CoachingProvider):
    """Test double that returns canned responses."""

    RESPONSES = {
        "hint": "Consider using a hash map to solve this problem.",
        "review": "Your code looks good, but consider edge cases like empty arrays.",
        "explain": "This is a classic problem that requires understanding of data structures.",
        "debug": "The issue appears to be in your loop condition. Check line 5.",
    }

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
        return {
            "summary": self.RESPONSES.get(
                mode, "Here's some guidance for your problem."
            ),
            "hints": [],
            "code_review": None,
            "complexity_analysis": None,
            "suggestions": [],
            "edge_cases": [],
            "explanation": None,
            "debug_help": None,
        }

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
        yield self.RESPONSES.get(mode, "Here's some guidance for your problem.")
