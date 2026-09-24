"""Consumer tests: family_compilers must read the visual metaphor registry (#286).

Issue #290 landed ``visual_metaphors.py``, but nothing consumed it — the
compiler still hardcodes palette, motion durations, base shapes and layout.
These tests are RED while the registry is dead code and go green only once
each family compiler resolves ``metaphor_for(family)`` at compile time and
derives those four decisions from the returned metaphor.

The golden pins (``test_family_golden_pins_286``) independently guarantee the
default-path output stays byte-identical, so consumer tests patching the
registry prove consultation without allowing behaviour drift.

``array``/``backtrack`` are excluded from the per-compiler checks: their
visuals are owned by ``AnimationCompiler`` and ``_compile_array`` merely
delegates — there are no hardcoded visuals in ``family_compilers`` to replace.
"""

import dataclasses
import json
import logging
import re
from pathlib import Path

import pytest

from app.services import family_compilers as fc
from app.services.trace_parser import parse_trace
from app.services.visual_metaphors import VisualMetaphor, metaphor_for

CONSUMABLE_FAMILIES = [
    "stack",
    "linked_list",
    "tree",
    "grid",
    "graph",
    "intervals",
]

# Minimal traces that compile today and exercise one highlighted visit, so a
# patched palette color or motion duration is observable in the output. The
# stack base-shape check uses _PUSH_TRACE — plates only exist after a push.
_VISIT_TRACES = {
    "stack": [
        '{"event":"init","data":["(",")"],"family":"stack"}',
        '{"event":"visit","i":0}',
        '{"event":"return","result":true}',
    ],
    "linked_list": [
        '{"event":"init","data":[1,2],"family":"linked_list"}',
        '{"event":"visit","i":0}',
        '{"event":"return","result":true}',
    ],
    "tree": [
        '{"event":"init","data":[1,2,3],"family":"tree"}',
        '{"event":"visit","i":0}',
        '{"event":"return","result":true}',
    ],
    "grid": [
        '{"event":"init","data":[[1,2],[3,4]],"family":"grid"}',
        '{"event":"visit","i":0,"j":0}',
        '{"event":"return","result":true}',
    ],
    "graph": [
        '{"event":"init","data":[[0,1],[1,0]],"family":"graph","n":2}',
        '{"event":"visit","i":0}',
        '{"event":"return","result":true}',
    ],
    "intervals": [
        '{"event":"init","data":[[1,3],[2,5]],"family":"intervals"}',
        '{"event":"visit","i":0}',
        '{"event":"return","result":true}',
    ],
}

_PUSH_TRACE = [
    '{"event":"init","data":["a","b"],"family":"stack"}',
    '{"event":"push","value":"a"}',
    '{"event":"return","result":1}',
]

_HIGHLIGHT_COLOR = "#ff0066"
_HIGHLIGHT_DURATION = 0.99


def _patch_metaphor(monkeypatch, family: str, **overrides) -> VisualMetaphor:
    """Serve a modified metaphor for ``family``; other families stay real."""
    real = metaphor_for(family)
    assert real is not None, f"registry must define {family}"
    patched = dataclasses.replace(real, **overrides)

    def fake(candidate, _family=family, _patched=patched):
        if candidate == _family:
            return _patched
        return metaphor_for(candidate)

    monkeypatch.setattr(fc, "metaphor_for", fake, raising=False)
    return patched


def _compile(family: str, lines) -> dict:
    animation = fc.compile_family(
        family, parse_trace("\n".join(lines)), title="consumer"
    )
    assert animation is not None, f"{family}: minimal consumer trace must compile"
    return animation


def _durations(animation: dict) -> set:
    return {
        op["duration"]
        for step in animation["steps"]
        for op in step["motion"]
        if "duration" in op
    }


def _shapes(animation: dict) -> list:
    return [s for step in animation["steps"] for s in step["shapes"]]


class TestRegistryIsOnTheLivePath:
    @pytest.mark.parametrize("family", CONSUMABLE_FAMILIES)
    def test_every_family_compiler_reads_palette_from_registry(
        self, monkeypatch, family
    ):
        real = metaphor_for(family)
        _patch_metaphor(
            monkeypatch,
            family,
            colors={**real.colors, "highlight_fill": _HIGHLIGHT_COLOR},
        )
        animation = _compile(family, _VISIT_TRACES[family])
        assert _HIGHLIGHT_COLOR in json.dumps(animation), (
            f"{family}: visit highlight must come from metaphor_for().colors, "
            "not a hardcoded constant"
        )

    @pytest.mark.parametrize("family", CONSUMABLE_FAMILIES)
    def test_every_family_compiler_reads_motion_from_registry(
        self, monkeypatch, family
    ):
        real = metaphor_for(family)
        _patch_metaphor(
            monkeypatch,
            family,
            motion_profile={
                **real.motion_profile,
                "highlight": {"duration": _HIGHLIGHT_DURATION},
            },
        )
        animation = _compile(family, _VISIT_TRACES[family])
        assert _HIGHLIGHT_DURATION in _durations(animation), (
            f"{family}: highlight duration must come from "
            "metaphor_for().motion_profile, not a hardcoded literal"
        )

    @pytest.mark.parametrize("family", CONSUMABLE_FAMILIES)
    def test_every_family_compiler_fails_safe_on_unknown_layout(
        self, monkeypatch, family
    ):
        _patch_metaphor(monkeypatch, family, layout="__missing_layout__")
        animation = fc.compile_family(
            family,
            parse_trace("\n".join(_VISIT_TRACES[family])),
            title="consumer",
        )
        assert animation is None, (
            f"{family}: the registry's layout must select the geometry "
            "builder — an unknown layout must fail safe (None), not be ignored"
        )

    def test_stack_compiler_uses_registry_base_shape(self, monkeypatch):
        _patch_metaphor(monkeypatch, "stack", base_shape="ellipse")
        animation = _compile("stack", _PUSH_TRACE)
        plates = [s for s in _shapes(animation) if s["id"].startswith("stack_cell_")]
        assert plates, "pushed plate shapes must render"
        assert all(s["type"] == "ellipse" for s in plates), (
            "stack plates must be drawn with metaphor_for().base_shape"
        )

    def test_graph_compiler_uses_registry_base_shape(self, monkeypatch):
        _patch_metaphor(monkeypatch, "graph", base_shape="rect")
        animation = _compile("graph", _VISIT_TRACES["graph"])
        nodes = [s for s in _shapes(animation) if s["id"].startswith("g_node_")]
        assert nodes, "graph node shapes must render"
        assert all(s["type"] == "rect" for s in nodes), (
            "graph nodes must be drawn with metaphor_for().base_shape"
        )

    def test_family_compilers_has_no_hardcoded_hex_colors(self):
        source = Path(fc.__file__).read_text()
        assert not re.search(r"#[0-9a-fA-F]{6}", source), (
            "family_compilers must source every color from the visual metaphor "
            "registry — hardcoded hex literals are what issue #286 removes"
        )


class TestMotionProfileDegradation:
    """A registry gap in motion timing must degrade, not crash the build (#286).

    Durations are cosmetic. Before the wiring, they were literals that could
    never fail; ``_duration`` reintroduced a KeyError path whose blast radius
    is the whole animation request. Missing roles fall back to the module
    default with a warning so the compile keeps serving.
    """

    def test_missing_motion_role_degrades_to_default_duration(self, caplog):
        with caplog.at_level(logging.WARNING, logger=fc.logger.name):
            duration = fc._duration({"intro": {"duration": 0.25}}, "appear")
        assert duration == 0.25, "a missing role must fall back to the default"
        assert any("appear" in record.getMessage() for record in caplog.records), (
            "the fallback must log which motion role was missing"
        )
