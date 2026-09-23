"""Golden pins for per-family compile output (#286 wiring half).

Characterization tests: one representative trace per animation family is
compiled with ``compile_family`` and its output (title, data, steps — the
beats the Motion Canvas viewer renders) is compared byte-for-byte against a
committed fixture. The fixtures were generated from the pre-wiring compiler
(branch ``refactor/286-visual-metaphor-consumption`` @ 4727aa8) and MUST stay
byte-identical while ``family_compilers`` is rewired onto the visual metaphor
registry: the wiring is a pure extraction with zero rendered-output change.

Each pin also re-validates through ``AnimationValidator`` so a fixture can
never silently encode an invalid scene.

Fixture files are machine-generated canonical JSON (sorted keys, compact
separators, trailing newline) and are excluded from prettier via
``.prettierignore`` so hooks never reformat them.

Regenerate ONLY for a deliberate, reviewed visual change:

    cd backend && python3 -c \
        "from tests.unit.test_family_golden_pins_286 import regenerate; regenerate()"
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from app.services.animation_validator import AnimationValidator
from app.services.family_compilers import FAMILY_COMPILERS, compile_family
from app.services.trace_parser import parse_trace

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "family_golden_286"

# case name -> (family, title, JSON-lines trace)
GOLDEN_TRACES: Dict[str, Tuple[str, str, List[str]]] = {
    "array": (
        "array",
        "Golden Bubble",
        [
            '{"event":"init","values":[3,1,2]}',
            '{"event":"compare","i":0,"j":1}',
            '{"event":"swap","i":0,"j":1}',
            '{"event":"compare","i":1,"j":2}',
            '{"event":"swap","i":1,"j":2}',
            '{"event":"mark","i":2,"state":"sorted"}',
            '{"event":"return","result":[1,2,3]}',
        ],
    ),
    "backtrack": (
        "backtrack",
        "Golden Subsets",
        [
            '{"event":"init","values":[1,2,3]}',
            '{"event":"choose","i":0}',
            '{"event":"choose","i":1}',
            '{"event":"backtrack","i":1}',
            '{"event":"choose","i":2}',
            '{"event":"return","result":[[1,2],[1,3]]}',
        ],
    ),
    "stack": (
        "stack",
        "Golden Valid Parens",
        [
            '{"event":"init","data":["(","(",")","]"],"family":"stack"}',
            '{"event":"push","value":"("}',
            '{"event":"push","value":"("}',
            '{"event":"pop","value":")"}',
            '{"event":"mark","i":0,"state":"paired"}',
            '{"event":"return","result":false}',
        ],
    ),
    "linked_list": (
        "linked_list",
        "Golden Reverse",
        [
            '{"event":"init","data":[1,2,3],"family":"linked_list"}',
            '{"event":"pointer","name":"prev","index":0}',
            '{"event":"visit","i":0}',
            '{"event":"pointer","name":"prev","index":1}',
            '{"event":"visit","i":1}',
            '{"event":"swap","i":0,"j":1}',
            '{"event":"write","i":2,"value":9}',
            '{"event":"mark","i":0,"state":"done"}',
            '{"event":"return","result":[3,2,1]}',
        ],
    ),
    "tree": (
        "tree",
        "Golden Max Depth",
        [
            '{"event":"init","data":[3,9,20,null,null,15,7],"family":"tree"}',
            '{"event":"pointer","name":"current","index":0}',
            '{"event":"visit","i":0}',
            '{"event":"visit","i":2}',
            '{"event":"pointer","name":"current","index":5}',
            '{"event":"mark","i":5,"state":"done"}',
            '{"event":"return","result":3}',
        ],
    ),
    "grid": (
        "grid",
        "Golden DP",
        [
            '{"event":"init","data":[[0,0,0],[0,0,0],[0,0,0]],"family":"grid"}',
            '{"event":"visit","i":0,"j":0}',
            '{"event":"read","i":0,"j":1}',
            '{"event":"backtrack","i":1,"j":0}',
            '{"event":"dp_update","i":1,"j":1,"value":5}',
            '{"event":"write","i":0,"j":0,"value":1}',
            '{"event":"mark","i":0,"j":0,"state":"done"}',
            '{"event":"return","result":5}',
        ],
    ),
    "graph": (
        "graph",
        "Golden Clone Graph",
        [
            '{"event":"init","data":[[2,4],[1,3],[2,4],[1,3]]}',
            '{"event":"visit","i":0}',
            '{"event":"edge","a":0,"b":1}',
            '{"event":"visit","i":1}',
            '{"event":"mark","i":0,"state":"done"}',
            '{"event":"return","result":4}',
        ],
    ),
    "graph_edge_list": (
        "graph",
        "Golden Courses",
        [
            '{"event":"init","data":[[0,1],[0,2],[2,1]],"family":"graph","n":3}',
            '{"event":"edge","a":0,"b":1}',
            '{"event":"edge","a":0,"b":2}',
            '{"event":"visit","i":0}',
            '{"event":"return","result":true}',
        ],
    ),
    "intervals": (
        "intervals",
        "Golden Merge",
        [
            '{"event":"init","data":[[1,3],[2,6],[8,10]],"family":"intervals"}',
            '{"event":"pointer","name":"i","index":0}',
            '{"event":"visit","i":0}',
            '{"event":"mark","i":0,"state":"merged"}',
            '{"event":"visit","i":1}',
            '{"event":"return","result":[[1,6],[8,10]]}',
        ],
    ),
}


def _canonical(animation: dict) -> str:
    """Canonical byte form of a compiled scene (sorted keys, compact)."""
    return json.dumps(animation, sort_keys=True, separators=(",", ":")) + "\n"


def compile_case(case: str) -> dict:
    """Compile one golden case (shared with the registry parity suite)."""
    family, title, lines = GOLDEN_TRACES[case]
    animation = compile_family(family, parse_trace("\n".join(lines)), title=title)
    assert animation is not None, f"{case}: golden trace must compile"
    return animation


def regenerate() -> None:
    """Rewrite every fixture from the current compiler output."""
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for case in GOLDEN_TRACES:
        (FIXTURE_DIR / f"{case}.json").write_text(_canonical(compile_case(case)))


@pytest.mark.parametrize("case", sorted(GOLDEN_TRACES), ids=sorted(GOLDEN_TRACES))
def test_compile_output_matches_golden_pin(case):
    animation = compile_case(case)
    validated, reason = AnimationValidator().validate(animation)
    assert validated is not None, f"{case}: golden scene must validate: {reason}"
    fixture_path = FIXTURE_DIR / f"{case}.json"
    assert fixture_path.exists(), f"missing fixture {fixture_path}"
    assert _canonical(animation) == fixture_path.read_text(), (
        f"{case}: compiled beats differ from the pre-wiring golden pin — "
        "the metaphor wiring must be byte-identical (see issue #286)"
    )


def test_every_animation_family_is_pinned():
    """The pin table must cover every registered family compiler."""
    pinned_families = {family for family, _, _ in GOLDEN_TRACES.values()}
    assert set(FAMILY_COMPILERS) <= pinned_families
