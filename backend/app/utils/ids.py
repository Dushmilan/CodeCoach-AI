"""Safe entity-ID validation.

Entity IDs (courses, modules, lessons) are used as filesystem directory and
URL segment components, so they must be restricted to a safe slug alphabet.
This prevents path-traversal (e.g. "../../backend") and other surprising IDs.
"""

import re

ENTITY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")


def validate_entity_id(entity_id: str, field: str = "id") -> str:
    """Validate an entity ID and return it unchanged.

    Raises ValueError if the ID is empty, non-string, or contains characters
    outside the safe slug alphabet (letters, digits, '-', '_').
    """
    if not isinstance(entity_id, str) or not entity_id:
        raise ValueError(f"{field} must be a non-empty string")
    if not ENTITY_ID_RE.match(entity_id):
        raise ValueError(
            f"{field} must be 1-100 chars using letters, digits, '_' or '-' "
            "(no '/', '\\\\', '..', or whitespace)"
        )
    return entity_id
