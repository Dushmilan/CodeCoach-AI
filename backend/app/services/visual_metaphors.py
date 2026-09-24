"""Visual Metaphor Registry — the compiler's visual vocabulary as data.

Each family maps to a metaphor (stack → plates, tree → roots and branches) plus
its base shape, layout, palette and motion profile. This registry is the
source of truth ``family_compilers`` reads at compile time: ``colors`` holds
the literal palette values, ``motion_profile`` maps semantic roles
(``highlight``, ``mark``, ``pointer``, ...) to the durations the compiler
emits, and ``layout``/``base_shape`` name the geometry and node shape the
compiler renders.

The parity suite in ``tests/unit/test_visual_metaphors.py``
(``TestRegistryMirrorsRenderedOutput``) pins every value — colors, base shape,
motion durations and layout — against what ``compile_family`` actually
renders, so the wiring half of #286 can consume this registry with
byte-identical output.

This module deliberately does not import ``family_compilers`` so that
``family_compilers`` can import it (one direction only, no cycle).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class VisualMetaphor:
    family: str
    metaphor: str
    base_shape: str
    layout: str
    colors: Dict[str, str]
    motion_profile: Dict[str, Dict[str, Any]] = field(default_factory=dict)


_BASE_COLORS: Dict[str, str] = {
    "idle_fill": "#1e293b",
    "idle_stroke": "#334155",
    "highlight_fill": "#1d4ed8",
    "highlight_stroke": "#3b82f6",
    "swap_fill": "#713f12",
    "accent": "#facc15",
    "active_fill": "#3b0764",
    "active_stroke": "#a855f7",
    "success_fill": "#14532d",
    "success_stroke": "#22c55e",
    "muted_stroke": "#475569",
    "arrow_stroke": "#64748b",
    "text": "#e2e8f0",
    "muted": "#0f172a",
}

# array/backtrack share one delegated compiler (AnimationCompiler); these roles
# document the durations that compiler emits for both families.
_DELEGATED_MOTION: Dict[str, Dict[str, Any]] = {
    "intro": {"duration": 0.25},
    "pointer": {"duration": 0.35},
    "highlight": {"duration": 0.25},
    "swap": {"duration": 0.45},
    "label": {"duration": 0.3},
    "mark_final": {"duration": 0.35},
    "mark": {"duration": 0.3},
    "choose": {"duration": 0.3},
    "reset": {"duration": 0.3},
    "outro": {"duration": 0.25},
}


def _delegated_motion() -> Dict[str, Dict[str, Any]]:
    """Fresh nested copy so families never share mutable profile dicts."""
    return {role: dict(spec) for role, spec in _DELEGATED_MOTION.items()}


_METAPHORS: Dict[str, VisualMetaphor] = {
    "array": VisualMetaphor(
        family="array",
        metaphor="row_of_cells",
        base_shape="rect",
        layout="horizontal_row",
        colors=dict(_BASE_COLORS),
        motion_profile=_delegated_motion(),
    ),
    "backtrack": VisualMetaphor(
        family="backtrack",
        metaphor="decision_tree",
        base_shape="rect",
        layout="horizontal_row",
        colors=dict(_BASE_COLORS),
        motion_profile=_delegated_motion(),
    ),
    "stack": VisualMetaphor(
        family="stack",
        metaphor="plates",
        base_shape="rect",
        layout="vertical_stack",
        colors=dict(_BASE_COLORS),
        motion_profile={
            "intro": {"duration": 0.25},
            "highlight": {"duration": 0.25},
            "appear": {"duration": 0.2},
            "exit": {"duration": 0.2},
            "move": {"duration": 0.4},
            "settle": {"duration": 0.3},
            "mark": {"duration": 0.3},
            "outro": {"duration": 0.25},
        },
    ),
    "linked_list": VisualMetaphor(
        family="linked_list",
        metaphor="chain",
        base_shape="rect",
        layout="horizontal_chain",
        colors=dict(_BASE_COLORS),
        motion_profile={
            "intro": {"duration": 0.25},
            "pointer": {"duration": 0.35},
            "highlight": {"duration": 0.25},
            "swap": {"duration": 0.45},
            "label": {"duration": 0.3},
            "mark": {"duration": 0.35},
            "outro": {"duration": 0.25},
        },
    ),
    "tree": VisualMetaphor(
        family="tree",
        metaphor="roots_and_branches",
        base_shape="rect",
        layout="reingold_tilford",
        colors=dict(_BASE_COLORS),
        motion_profile={
            "intro": {"duration": 0.25},
            "pointer": {"duration": 0.35},
            "highlight": {"duration": 0.25},
            "mark": {"duration": 0.35},
            "outro": {"duration": 0.25},
        },
    ),
    "graph": VisualMetaphor(
        family="graph",
        metaphor="network",
        base_shape="ellipse",
        layout="circular_force",
        colors=dict(_BASE_COLORS),
        motion_profile={
            "intro": {"duration": 0.25},
            "highlight": {"duration": 0.25},
            "edge": {"duration": 0.3},
            "mark": {"duration": 0.3},
            "outro": {"duration": 0.25},
        },
    ),
    "grid": VisualMetaphor(
        family="grid",
        metaphor="chessboard",
        base_shape="rect",
        layout="grid",
        colors=dict(_BASE_COLORS),
        motion_profile={
            "intro": {"duration": 0.25},
            "highlight": {"duration": 0.25},
            "reset": {"duration": 0.25},
            "commit": {"duration": 0.3},
            "mark": {"duration": 0.3},
            "outro": {"duration": 0.25},
        },
    ),
    "intervals": VisualMetaphor(
        family="intervals",
        metaphor="timeline_bars",
        base_shape="rect",
        layout="horizontal_tracks",
        colors=dict(_BASE_COLORS),
        motion_profile={
            "intro": {"duration": 0.25},
            "highlight": {"duration": 0.25},
            "mark": {"duration": 0.3},
            "outro": {"duration": 0.25},
        },
    ),
}


def metaphor_for(family: Optional[str]) -> Optional[VisualMetaphor]:
    return _METAPHORS.get(family) if family else None
