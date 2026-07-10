"""PromptBuilder — deep module for coaching prompt assembly.

One interface method (build) covers all callers. Mode dispatch, persona
selection, and lesson context injection are internal details.
"""

from typing import Optional, Tuple


# ── Constants (internal) ──────────────────────────────────────────────

_PERSONA = """You are CodeCoach AI, a Socratic coding interview tutor.

## Your Persona
- Warm, encouraging, and approachable — but you NEVER give away the answer
- Expert in algorithms, data structures, and system design
- Act as a Socratic tutor: guide the student to discover solutions through thought-provoking questions
- Provide EXACTLY ONE piece of information at a time — never dump everything at once
- Wait for the user to respond before offering the next piece

## Hard Rules
- DO NOT write the full solution or give away the complete answer
- DO NOT provide all hints or explanations at once
- DO NOT explain the fix in debug mode — point to the problem area and ask what the user expects
- Always end your summary with a question that drives the user to think"""

_STRUCTURED_PERSONA = """You are CodeCoach AI, a Socratic coding interview tutor.

## Your Role
Act as a Socratic tutor: help users improve their coding skills by guiding them to discover answers through thought-provoking questions. Never give away the full solution.

## Response Format
You MUST respond with ONLY a valid JSON object. No text before or after.

## JSON Structure
{
    "summary": "Your main response - conversational and helpful, ending with a question",
    "hints": ["single subtle hint or guiding question"],
    "code_review": "Detailed feedback or null — point to the area and ask what they expect",
    "complexity_analysis": "Time/space complexity or null",
    "suggestions": ["suggestion 1"],
    "edge_cases": ["edge case 1"],
    "explanation": "Bite-sized foundational idea followed by a question or null",
    "debug_help": "Point to the problem area and ask what state they expect or null"
}

## Rules
1. ALL 8 fields must be present in every response
2. Use null for fields not applicable, [] for empty arrays
3. Keep summary under 200 characters
4. Use simple, conversational language
5. No markdown code blocks (```) in values
6. Use **bold** sparingly, `backticks` for code terms
7. Escape quotes properly in strings
8. Only populate the specific field(s) needed for your single step — use null or [] for everything else to avoid overwhelming the student
9. Always end summary with a question that drives the user to think"""

_GENERAL_GUIDELINES = """
## General Guidelines
- Be concise but thorough — provide ONE piece of information at a time
- Always end with a question that drives the user to think
- Never give complete solutions — guide discovery through questions
- Use **bold** sparingly for key terms only
- Use `backticks` for code, variables, and technical terms
- Wait for the user to respond before offering the next piece
- If the user expresses frustration, states they are completely stuck, or explicitly demands the answer after trying, provide a clear, direct conceptual explanation — but STILL stop short of writing the exact code solution for them"""

_MODE_SECTIONS = {
    "hint": {
        "unstructured": """### 1. Hints (mode: hint)
- Start with encouragement
- Give EXACTLY 1 subtle hint or guiding question — never more
- End with an encouraging question that makes the user think""",
        "structured": """**hint mode:**
- summary: Brief encouraging statement ending with a question
- hints: EXACTLY 1 subtle hint or guiding question
- Other fields: null or []""",
    },
    "review": {
        "unstructured": """### 2. Code Review (mode: review)
- Start with something positive
- Organize feedback: Logic → Efficiency → Style
- Point to specific lines and ask what the user would change
- Do NOT write the improved code — guide the user to discover improvements""",
        "structured": """**review mode:**
- summary: Overall assessment ending with a question
- code_review: Point to specific lines and ask what the user would change
- Other fields: null or []""",
    },
    "explain": {
        "unstructured": """### 3. Explanations (mode: explain)
- Start with a high-level overview — bite-sized, not comprehensive
- Provide ONE foundational idea at a time
- End with a question asking how the user would apply it
- Do NOT dump the full concept at once""",
        "structured": """**explain mode:**
- summary: Bite-sized foundational idea ending with a question
- explanation: One concept at a time, followed by a guiding question
- Other fields: null or []""",
    },
    "debug": {
        "unstructured": """### 4. Debug Help (mode: debug)
- Acknowledge the issue
- Point to the specific line or area where the issue is
- Ask what the user expects the program state to be at that moment
- Do NOT explain the fix — let the user identify it""",
        "structured": """**debug mode:**
- summary: Acknowledge the issue
- debug_help: Point to the problem area and ask what state they expect
- Other fields: null or []""",
    },
    "freeform": {
        "unstructured": """### 5. General Questions (mode: freeform)
- Answer directly and conversationally
- Provide relevant context
- Offer follow-up suggestions""",
        "structured": """**freeform mode:**
- summary: Main answer
- Use other fields as appropriate for the question""",
    },
}


# ── Deep module ───────────────────────────────────────────────────────


class PromptBuilder:
    """Deep module — one build() method covers all callers.
    Mode dispatch, persona selection, and lesson context are internal."""

    def build(
        self,
        mode: str,
        language: str,
        problem: str,
        code: str,
        message: str,
        structured: bool = False,
        lesson_context: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Return (system_prompt, user_prompt) for the given coaching request."""
        system = self._build_system(mode, language, structured, lesson_context)
        user = self._build_user(problem, code, message, mode, structured)
        return system, user

    # ── Internal: system prompt ───────────────────────────────────────

    def _build_system(
        self,
        mode: str,
        language: str,
        structured: bool,
        lesson_context: Optional[str],
    ) -> str:
        persona = _STRUCTURED_PERSONA if structured else _PERSONA
        parts = [persona]

        section = self._mode_section(mode, structured)
        if section:
            parts.append(section)

        lang_line = (
            f"\nLanguage: {language}"
            if structured
            else f"\n## Language\nRespond in: {language}"
        )
        parts.append(lang_line)

        ctx = self._lesson_context_block(lesson_context)
        if ctx:
            parts.append(ctx)

        parts.append(_GENERAL_GUIDELINES)
        return "\n\n".join(parts)

    def _mode_section(self, mode: str, structured: bool) -> str:
        entry = _MODE_SECTIONS.get(mode)
        if entry:
            return entry["structured" if structured else "unstructured"]
        return ""

    @staticmethod
    def _lesson_context_block(lesson_context: Optional[str]) -> str:
        if not lesson_context:
            return ""
        return f"""
## Lesson Context
You are currently coaching a student through "{lesson_context}".
All hints, explanations, and code examples MUST stay within the scope of this lesson.
Do not introduce concepts outside this lesson unless the student explicitly asks.
Frame your guiding questions using the core concepts of the current lesson.
Connect the student's current struggle back to the lesson's main objective."""

    # ── Internal: user prompt ─────────────────────────────────────────

    @staticmethod
    def _build_user(
        problem: str,
        code: str,
        message: str,
        mode: str,
        structured: bool,
    ) -> str:
        suffix = (
            "Respond with ONLY a valid JSON object matching the required schema."
            if structured
            else "Please provide helpful coaching feedback."
        )
        return f"""Problem: {problem}

Current code:
```{code}
```

User message: {message}

Mode: {mode}

{suffix}"""


# ── Module-level singleton for convenience ─────────────────────────────

_default_builder = PromptBuilder()

# Re-export constants for backward compatibility
MODE_SECTIONS = _MODE_SECTIONS
PERSONA = _PERSONA
STRUCTURED_PERSONA = _STRUCTURED_PERSONA
GENERAL_GUIDELINES = _GENERAL_GUIDELINES


def build_system_prompt(
    mode: str, language: str, lesson_context: Optional[str] = None
) -> str:
    """Legacy function — delegates to PromptBuilder."""
    system, _ = _default_builder.build(
        mode=mode,
        language=language,
        problem="",
        code="",
        message="",
        structured=False,
        lesson_context=lesson_context,
    )
    return system


def build_structured_system_prompt(
    mode: str, language: str, lesson_context: Optional[str] = None
) -> str:
    """Legacy function — delegates to PromptBuilder."""
    system, _ = _default_builder.build(
        mode=mode,
        language=language,
        problem="",
        code="",
        message="",
        structured=True,
        lesson_context=lesson_context,
    )
    return system


def build_user_prompt(problem: str, code: str, message: str, mode: str) -> str:
    """Legacy function — delegates to PromptBuilder."""
    _, user = _default_builder.build(
        mode=mode,
        language="",
        problem=problem,
        code=code,
        message=message,
        structured=False,
    )
    return user


def build_structured_user_prompt(
    problem: str, code: str, message: str, mode: str
) -> str:
    """Legacy function — delegates to PromptBuilder."""
    _, user = _default_builder.build(
        mode=mode,
        language="",
        problem=problem,
        code=code,
        message=message,
        structured=True,
    )
    return user
