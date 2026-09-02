"""Mock coaching provider for tests."""

from typing import AsyncIterator, Dict, Any, Optional

from app.ports.coaching_provider import CoachingProvider

LINEAR_SEARCH_ANIMATION = {
    "title": "Searching for 4",
    "data": {"values": [5, 1, 2, 3, 4, 6], "target": 4},
    "steps": [
        {
            "narration": "5 is not the target, continue searching.",
            "shapes": [
                {
                    "id": "cell_0",
                    "type": "rect",
                    "x": -240,
                    "y": 0,
                    "width": 88,
                    "height": 88,
                    "radius": 12,
                    "fill": "#1e293b",
                    "stroke": "#334155",
                },
                {
                    "id": "val_0",
                    "type": "text",
                    "x": -240,
                    "y": 0,
                    "text": "5",
                    "fontSize": 34,
                    "fill": "#94a3b8",
                },
                {
                    "id": "ptr",
                    "type": "polygon",
                    "points": [[-12, -30], [0, -60], [12, -30]],
                    "x": -240,
                    "y": -80,
                    "fill": "#facc15",
                },
            ],
            "motion": [
                {"target": "cell_0", "op": "appear", "duration": 0.25},
                {"target": "val_0", "op": "appear", "duration": 0.25},
                {"target": "ptr", "op": "appear", "duration": 0.25},
            ],
        },
        {
            "narration": "Moving the pointer past the next element.",
            "motion": [
                {"target": "ptr", "op": "move", "to": [0, -80], "duration": 0.35},
            ],
        },
        {
            "narration": "Found the target 4 at index 4.",
            "shapes": [
                {
                    "id": "cell_4",
                    "type": "rect",
                    "x": 240,
                    "y": 0,
                    "width": 88,
                    "height": 88,
                    "radius": 12,
                    "fill": "#14532d",
                    "stroke": "#22c55e",
                },
                {
                    "id": "val_4",
                    "type": "text",
                    "x": 240,
                    "y": 0,
                    "text": "4",
                    "fontSize": 34,
                    "fill": "#ffffff",
                },
            ],
            "motion": [
                {"target": "cell_4", "op": "appear", "duration": 0.25},
                {"target": "val_4", "op": "appear", "duration": 0.25},
                {"target": "ptr", "op": "move", "to": [240, -80], "duration": 0.35},
            ],
        },
    ],
}


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
        initial_code: Optional[str] = None,
        learner_context: Optional[str] = None,
        submission_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {
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
        if mode == "animate":
            data["animation"] = LINEAR_SEARCH_ANIMATION
        return data

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
        return LINEAR_SEARCH_ANIMATION

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
        yield self.RESPONSES.get(mode, "Here's some guidance for your problem.")
