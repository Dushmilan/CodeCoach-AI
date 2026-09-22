"""Visual Metaphor Registry — the compiler's visual vocabulary as data.

Each family maps to a metaphor (stack → plates, tree → roots and branches) plus
its base shape, layout, palette and motion profile. Colors are literal values
mirroring the current ``family_compilers`` palette; a parity test pins them, and
workstream D makes the compiler consume this registry with no output change.

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
    "accent": "#facc15",
    "success_fill": "#14532d",
    "success_stroke": "#22c55e",
    "text": "#e2e8f0",
    "muted": "#0f172a",
}

_METAPHORS: Dict[str, VisualMetaphor] = {
    "array": VisualMetaphor(
        family="array",
        metaphor="row_of_cells",
        base_shape="rect",
        layout="horizontal_row",
        colors=dict(_BASE_COLORS),
    ),
    "backtrack": VisualMetaphor(
        family="backtrack",
        metaphor="decision_tree",
        base_shape="ellipse",
        layout="reingold_tilford",
        colors=dict(_BASE_COLORS),
    ),
    "stack": VisualMetaphor(
        family="stack",
        metaphor="plates",
        base_shape="rect",
        layout="vertical_stack",
        colors=dict(_BASE_COLORS),
    ),
    "linked_list": VisualMetaphor(
        family="linked_list",
        metaphor="chain",
        base_shape="ellipse",
        layout="horizontal_chain",
        colors=dict(_BASE_COLORS),
    ),
    "tree": VisualMetaphor(
        family="tree",
        metaphor="roots_and_branches",
        base_shape="ellipse",
        layout="reingold_tilford",
        colors=dict(_BASE_COLORS),
    ),
    "graph": VisualMetaphor(
        family="graph",
        metaphor="network",
        base_shape="ellipse",
        layout="circular_force",
        colors=dict(_BASE_COLORS),
    ),
    "grid": VisualMetaphor(
        family="grid",
        metaphor="chessboard",
        base_shape="rect",
        layout="grid",
        colors=dict(_BASE_COLORS),
    ),
    "intervals": VisualMetaphor(
        family="intervals",
        metaphor="timeline_bars",
        base_shape="rect",
        layout="horizontal_tracks",
        colors=dict(_BASE_COLORS),
    ),
}


def metaphor_for(family: Optional[str]) -> Optional[VisualMetaphor]:
    return _METAPHORS.get(family) if family else None
