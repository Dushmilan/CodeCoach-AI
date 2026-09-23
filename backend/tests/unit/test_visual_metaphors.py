"""Unit tests for the visual metaphor registry (#240).

The registry must mirror the compiler's current palette exactly so workstream D
can flip family_compilers onto it with zero rendered-output change.

The ``TestRegistryMirrorsRenderedOutput`` suite (added by #286) pins the full
parity contract: colors, base shape, motion durations and layout geometry are
all checked against what ``compile_family`` actually renders.
"""

import math

import pytest

from app.services import family_compilers as fc
from app.services.visual_metaphors import metaphor_for
from tests.unit import test_family_golden_pins_286 as golden

FAMILIES = [
    "array",
    "backtrack",
    "stack",
    "linked_list",
    "tree",
    "graph",
    "grid",
    "intervals",
]


class TestMetaphorRegistry:
    @pytest.mark.parametrize("family", FAMILIES)
    def test_every_family_has_a_metaphor(self, family):
        metaphor = metaphor_for(family)
        assert metaphor is not None
        assert metaphor.family == family
        assert metaphor.base_shape in {"rect", "ellipse", "polygon"}
        assert metaphor.layout
        assert metaphor.metaphor

    def test_colors_mirror_compiler_palette(self):
        colors = metaphor_for("array").colors
        assert colors["idle_fill"] == fc.IDLE_FILL
        assert colors["idle_stroke"] == fc.IDLE_STROKE
        assert colors["highlight_fill"] == fc.CHECK_FILL
        assert colors["highlight_stroke"] == fc.CHECK_STROKE
        assert colors["accent"] == fc.SWAP_STROKE
        assert colors["success_fill"] == fc.DONE_FILL
        assert colors["success_stroke"] == fc.DONE_STROKE
        assert colors["text"] == fc.TEXT_FILL

    def test_unknown_family_is_none(self):
        assert metaphor_for("nope") is None


# ── wiring-half parity suite (#286): the registry must mirror what the ──────
# compiler ACTUALLY renders — colors, node base shape, motion durations and
# layout geometry — so family_compilers can consume it with byte-identical
# output. Compiled scenes come from the shared golden traces/fixtures.

# compiler module constant -> registry color key (all 12 must be covered)
_PALETTE_MAP = {
    "idle_fill": "IDLE_FILL",
    "idle_stroke": "IDLE_STROKE",
    "highlight_fill": "CHECK_FILL",
    "highlight_stroke": "CHECK_STROKE",
    "swap_fill": "SWAP_FILL",
    "accent": "SWAP_STROKE",
    "success_fill": "DONE_FILL",
    "success_stroke": "DONE_STROKE",
    "active_fill": "ACTIVE_FILL",
    "active_stroke": "ACTIVE_STROKE",
    "text": "TEXT_FILL",
    "muted": "MUTED_FILL",
}

# family -> id prefix of its primary rendered data node
_NODE_PREFIX = {
    "array": "cell_",
    "backtrack": "cell_",
    "stack": "stack_cell_",
    "linked_list": "node_",
    "tree": "node_",
    "graph": "g_node_",
    "grid": "cell_",
    "intervals": "bar_",
}


def _rendered_nodes(family: str) -> list:
    animation = golden.compile_case(family)
    prefix = _NODE_PREFIX[family]
    nodes = [
        shape
        for step in animation["steps"]
        for shape in step["shapes"]
        if shape["id"].startswith(prefix) and shape.get("type") != "text"
    ]
    # Final positions: a later move op overrides the spawn position (stack
    # plates spawn below the container and are moved onto the stack).
    final = {
        op["target"]: op["to"]
        for step in animation["steps"]
        for op in step["motion"]
        if op["op"] == "move" and "to" in op
    }
    for node in nodes:
        if node["id"] in final:
            node["x"], node["y"] = final[node["id"]]
    return nodes


def _rendered_durations(family: str) -> set:
    animation = golden.compile_case(family)
    return {
        op["duration"]
        for step in animation["steps"]
        for op in step["motion"]
        if "duration" in op
    }


# geometry invariants that define each registry layout name, checked against
# the compiler's rendered node positions (distinguishes the claimed layout
# from the other layouts in the registry)
def _horizontal_row_geometry(nodes: list) -> bool:
    ys = {n["y"] for n in nodes}
    return len(ys) == 1 and len({n["x"] for n in nodes}) > 1


def _horizontal_chain_geometry(nodes: list) -> bool:
    xs = sorted({n["x"] for n in nodes})
    ys = {n["y"] for n in nodes}
    gaps = {round(b - a, 2) for a, b in zip(xs, xs[1:])}
    return len(ys) == 1 and len(xs) >= 3 and len(gaps) == 1


def _vertical_stack_geometry(nodes: list) -> bool:
    xs = {n["x"] for n in nodes}
    return len(xs) == 1 and len({n["y"] for n in nodes}) > 1


def _reingold_tilford_geometry(nodes: list) -> bool:
    by_index = {int(n["id"].rsplit("_", 1)[-1]): n for n in nodes}
    for i, node in by_index.items():
        parent = (i - 1) // 2
        if parent in by_index and parent >= 0:
            p = by_index[parent]
            if node["x"] != p["x"] and node["y"] > p["y"]:
                return True
    return False


def _circular_force_geometry(nodes: list) -> bool:
    if len(nodes) < 2:
        return False
    radii = {round(math.hypot(n["x"], n["y"]), 1) for n in nodes}
    return len(radii) == 1 and next(iter(radii)) > 0


def _grid_geometry(nodes: list) -> bool:
    xs = sorted({n["x"] for n in nodes})
    ys = sorted({n["y"] for n in nodes})
    x_gaps = {round(b - a, 2) for a, b in zip(xs, xs[1:])}
    y_gaps = {round(b - a, 2) for a, b in zip(ys, ys[1:])}
    return len(xs) >= 2 and len(ys) >= 2 and len(x_gaps) == 1 and len(y_gaps) == 1


def _horizontal_tracks_geometry(nodes: list) -> bool:
    ys = [n["y"] for n in nodes]
    return len(ys) >= 2 and len(set(ys)) == len(ys) and len({n["x"] for n in nodes}) > 1


_LAYOUT_GEOMETRY = {
    "horizontal_row": _horizontal_row_geometry,
    "horizontal_chain": _horizontal_chain_geometry,
    "vertical_stack": _vertical_stack_geometry,
    "reingold_tilford": _reingold_tilford_geometry,
    "circular_force": _circular_force_geometry,
    "grid": _grid_geometry,
    "horizontal_tracks": _horizontal_tracks_geometry,
}


class TestRegistryMirrorsRenderedOutput:
    def test_registry_colors_cover_every_compiler_palette_constant(self):
        colors = metaphor_for("array").colors
        for key, constant in _PALETTE_MAP.items():
            assert key in colors, (
                f"registry colors missing {key!r} "
                f"(compiler palette constant {constant})"
            )
            assert colors[key] == getattr(fc, constant), key

    def test_registry_colors_cover_structural_line_colors(self):
        colors = metaphor_for("linked_list").colors
        assert colors["muted_stroke"] == "#475569"  # null node + tree/graph edges
        assert colors["arrow_stroke"] == "#64748b"  # linked-list arrows

    @pytest.mark.parametrize("family", FAMILIES)
    def test_registry_base_shape_matches_rendered_nodes(self, family):
        nodes = _rendered_nodes(family)
        assert nodes, f"{family}: golden scene must render data nodes"
        rendered_types = {n["type"] for n in nodes}
        assert rendered_types == {metaphor_for(family).base_shape}, (
            f"{family}: registry base_shape "
            f"{metaphor_for(family).base_shape!r} does not match rendered "
            f"node type(s) {sorted(rendered_types)}"
        )

    @pytest.mark.parametrize("family", FAMILIES)
    def test_registry_motion_profile_covers_rendered_durations(self, family):
        rendered = _rendered_durations(family)
        profile = metaphor_for(family).motion_profile
        documented = {float(role["duration"]) for role in profile.values()}
        missing = rendered - documented
        assert not missing, (
            f"{family}: rendered duration(s) {sorted(missing)} are not "
            "documented in the registry motion_profile — every emitted "
            "duration must be registry-sourced"
        )

    @pytest.mark.parametrize("family", FAMILIES)
    def test_registry_layout_matches_rendered_geometry(self, family):
        layout = metaphor_for(family).layout
        assert layout in _LAYOUT_GEOMETRY, f"unknown layout {layout!r}"
        nodes = _rendered_nodes(family)
        assert _LAYOUT_GEOMETRY[layout](nodes), (
            f"{family}: registry layout {layout!r} does not match the "
            "geometry the compiler actually renders"
        )
