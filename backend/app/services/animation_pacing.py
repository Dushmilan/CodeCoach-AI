"""Role-aware pacing for animation beats.

The scene planner tags each beat with a transient ``role``; this module rewrites
the beat's motion durations to give the timeline cinematic weight, then removes
the tag so it never reaches the validated script. Beats without a role keep
their durations (no behaviour change).
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

MIN_DURATION = 0.1
MAX_DURATION = 5.0

_ROLES = ("intro", "loop", "climax", "outro")


@dataclass(frozen=True)
class PacingProfile:
    intro: float = 0.25
    loop: float = 0.35
    climax: float = 0.5
    outro: float = 0.25


DEFAULT_PROFILE = PacingProfile()


def _clamp(value: float) -> float:
    return max(MIN_DURATION, min(MAX_DURATION, float(value)))


def apply_pacing(
    beats: Optional[List[Dict[str, Any]]],
    profile: PacingProfile = DEFAULT_PROFILE,
) -> Optional[List[Dict[str, Any]]]:
    """Rewrite each beat's motion durations by its ``role``, then strip ``role``."""
    if not isinstance(beats, list):
        return beats
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        role = beat.pop("role", None)
        if role not in _ROLES:
            continue
        duration = _clamp(getattr(profile, role))
        motion = beat.get("motion")
        if not isinstance(motion, list):
            continue
        for op in motion:
            if isinstance(op, dict) and "duration" in op:
                op["duration"] = duration
    return beats
