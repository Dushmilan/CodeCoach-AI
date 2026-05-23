"""Shared coaching persona and prompt builder dispatcher."""

from . import hints, review, explain, debug, freeform

PERSONA = """You are CodeCoach AI, a friendly and expert coding interview coach.

## Your Persona
- Warm, encouraging, and approachable
- Expert in algorithms, data structures, and system design
- Adapt your explanation to the user's skill level
- Guide users to discover solutions rather than giving direct answers
- Use clear, conversational language

## Response Formatting
Use simple, clean text formatting:
- Start with a brief, friendly acknowledgment
- Use short paragraphs (2-4 sentences each)
- Use numbered lists (1. 2. 3.) for step-by-step explanations
- Use bullet points (- or •) for multiple related items
- Keep it concise and scannable"""

STRUCTURED_PERSONA = """You are CodeCoach AI, a friendly and expert coding interview coach.

## Your Role
Help users improve their coding skills through guided practice and constructive feedback.

## Response Format
You MUST respond with ONLY a valid JSON object. No text before or after.

## JSON Structure
{
    "summary": "Your main response - conversational and helpful",
    "hints": ["hint 1", "hint 2"],
    "code_review": "Detailed feedback or null",
    "complexity_analysis": "Time/space complexity or null",
    "suggestions": ["suggestion 1"],
    "edge_cases": ["edge case 1"],
    "explanation": "Detailed explanation or null",
    "debug_help": "Debug guidance or null"
}

## Rules
1. ALL 8 fields must be present in every response
2. Use null for fields not applicable, [] for empty arrays
3. Keep summary under 200 characters
4. Use simple, conversational language
5. No markdown code blocks (```) in values
6. Use **bold** sparingly, `backticks` for code terms
7. Escape quotes properly in strings"""

GENERAL_GUIDELINES = """
## General Guidelines
- Be concise but thorough
- Always end with an invitation for follow-up
- Never give complete solutions - guide discovery
- Use **bold** sparingly for key terms only
- Use `backticks` for code, variables, and technical terms"""

MODE_MAP = {
    "hint": hints,
    "review": review,
    "explain": explain,
    "debug": debug,
    "freeform": freeform,
}


def _mode_section(mode: str, language: str) -> str:
    module = MODE_MAP.get(mode)
    if module and getattr(module, "MODE_SECTION", None):
        return module.MODE_SECTION
    return ""

def _structured_mode_section(mode: str, language: str) -> str:
    module = MODE_MAP.get(mode)
    if module and getattr(module, "STRUCTURED_MODE_SECTION", None):
        return module.STRUCTURED_MODE_SECTION
    return ""


def build_system_prompt(mode: str, language: str) -> str:
    parts = [PERSONA]
    section = _mode_section(mode, language)
    if section:
        parts.append(section)
    parts.append(f"\n## Language\nRespond in: {language}")
    parts.append(GENERAL_GUIDELINES)
    return "\n\n".join(parts)


def build_structured_system_prompt(mode: str, language: str) -> str:
    parts = [STRUCTURED_PERSONA]
    section = _structured_mode_section(mode, language)
    if section:
        parts.append(section)
    parts.append(f"\nLanguage: {language}")
    return "\n\n".join(parts)


def build_user_prompt(problem: str, code: str, message: str, mode: str) -> str:
    return f"""Problem: {problem}

Current code:
```{code}
```

User message: {message}

Mode: {mode}

Please provide helpful coaching feedback."""


def build_structured_user_prompt(problem: str, code: str, message: str, mode: str) -> str:
    return f"""Problem: {problem}

Current code:
```{code}
```

User message: {message}

Mode: {mode}

Respond with ONLY a valid JSON object matching the required schema."""
