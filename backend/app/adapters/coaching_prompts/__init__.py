"""Coaching prompt templates per mode.

Each module exports a MODE_SYSTEM_PROMPT and a MODE_STRUCTURED_SYSTEM_PROMPT
(or None if not applicable).
"""

from .base import build_system_prompt, build_structured_system_prompt, build_user_prompt, build_structured_user_prompt

__all__ = [
    "build_system_prompt",
    "build_structured_system_prompt",
    "build_user_prompt",
    "build_structured_user_prompt",
]
