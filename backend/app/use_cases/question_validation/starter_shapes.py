"""Shared coercion for union-typed ``Question.starter`` shapes.

``Question.starter`` is typed ``StarterCode | str | list | dict``: the
schema's ``normalize_starter`` turns language-name strings and list/dict
shapes into a model on the validated path, but plain strings survive and
unvalidated shapes (``model_construct``/``model_copy``) can arrive as
list/dict. Every use case that reads per-language starter code must go
through :func:`starter_code_for` instead of dereferencing
``question.starter.<language>`` directly, or non-model starters crash with
``AttributeError``. Coercion mirrors ``normalize_starter`` at the narrowest
boundary; the shared ``Question`` schema is untouched.
"""

from typing import Any, Dict, List, Union

from app.models.schemas import StarterCode


def starter_code_for(
    starter: Union[StarterCode, str, List, Dict[str, Any], None],
    language: str,
) -> str:
    """Return the starter code for ``language``, coercing union shapes.

    Model -> its per-language attribute, dict -> its language entry, list ->
    the entry whose ``language`` matches, anything else (str, None, ...) ->
    ``""`` (treated as absent, exactly like the historic
    ``getattr(starter, lang, None)`` fallback). Non-string entries coerce to
    ``""`` so downstream ``re``/``strip`` calls never see a non-``str``.
    """
    if isinstance(starter, StarterCode):
        code = getattr(starter, language, "")
        return code if isinstance(code, str) else ""
    if isinstance(starter, dict):
        code = starter.get(language, "")
        return code if isinstance(code, str) else ""
    if isinstance(starter, list):
        for entry in starter:
            if (
                isinstance(entry, dict)
                and entry.get("language") == language
                and isinstance(entry.get("code"), str)
            ):
                return entry["code"]
        return ""
    return ""
