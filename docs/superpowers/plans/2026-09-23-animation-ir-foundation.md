# Animation IR Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the additive shared contracts (trace line capture, display-code mapping, beat-IR fields, pacing and metaphor interfaces) that workstreams A/B/C/D build on, with no behaviour change to existing animations.

**Architecture:** Extend `trace_instrumenter.py` to record each `__trace` call's source line and to derive clean display code; extend `trace_parser.TraceEvent` and `AnimationStepSpec` with optional fields; add two standalone service modules (`animation_pacing`, `visual_metaphors`) with pure interfaces. Nothing in the canonical pipeline changes behaviour — every new field is optional and ignored by the existing validator.

**Tech Stack:** Python 3.11+, Pydantic 2.13, pytest 8.4, FastAPI service layer.

**Spec:** `docs/superpowers/specs/2026-09-23-animation-deterministic-pedagogy-design.md`

## Global Constraints

- Python only; PostgreSQL/DB untouched by this plan (no schema change).
- All new IR fields are **optional**; existing callers must keep working unchanged.
- Validator bounds: durations 0.1–5.0s; shapes `rect|ellipse|line|polygon|text`.
- `AnimationStepSpec.line` is 1-based, `ge=1`.
- Tests import `app.*` and run from `backend/`.
- TDD: red → green → refactor; every source change has a failing test first.

## Review Focus

- Multi-line `__trace(...)` call: the full statement span is stripped and mapped, not just its first line.
- `__trace` used as a non-statement (assigned, nested): must NOT be stripped.
- `display_code_and_map` on syntactically invalid code: returns identity mapping, never raises.
- Trace `line` present but `0`, negative, `"4"`, or `True`: dropped, never coerced.
- Pacing value outside 0.1–5.0s: clamped so the validator stays green.

---

### Task F1: Trace events carry a source line

**Files:**
- Modify: `backend/app/services/trace_parser.py`
- Test: `backend/tests/unit/test_trace_parser.py`

**Interfaces:**
- Produces: `TraceEvent.line -> Optional[int]` (typed accessor, `None` when absent/invalid).

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_trace_parser.py`:

```python
class TestTraceLine:
    def test_parses_valid_line(self):
        events = parse_trace(_line("compare", i=0, j=1, line=7))
        assert events[0].line == 7

    def test_absent_line_is_none(self):
        events = parse_trace(_line("compare", i=0, j=1))
        assert events[0].line is None

    @pytest.mark.parametrize("bad", [0, -3, "4", True])
    def test_invalid_line_is_dropped(self, bad):
        events = parse_trace(_line("compare", i=0, j=1, line=bad))
        assert events[0].line is None
        assert "line" not in events[0].fields
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/unit/test_trace_parser.py::TestTraceLine -p no:cacheprovider --no-cov -q`
Expected: FAIL — `AttributeError: line` (no accessor) / invalid line still in fields.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/services/trace_parser.py`, add a `line` property to `TraceEvent`:

```python
    @property
    def line(self) -> Optional[int]:
        """1-based source line in the canonical solution, or None."""
        value = self.fields.get("line")
        return value if isinstance(value, int) and not isinstance(value, bool) else None
```

In `_parse_payload`, after `fields.pop("event", None)`, sanitize the line:

```python
    line = fields.get("line")
    if isinstance(line, bool) or not isinstance(line, int) or line <= 0:
        fields.pop("line", None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/unit/test_trace_parser.py -p no:cacheprovider --no-cov -q`
Expected: PASS (all existing parser tests plus the new class).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/trace_parser.py backend/tests/unit/test_trace_parser.py
git commit -m "feat(animation): carry source line on trace events (#240)"
```

---

### Task F2: Instrumenter records the caller line

**Files:**
- Modify: `backend/app/services/trace_instrumenter.py`
- Test: `backend/tests/unit/test_trace_instrumenter.py`

**Interfaces:**
- Produces: `_build_helper() -> str`; wrapped code emits `"line"` (1-based, relative to the canonical solution) on every event.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_trace_instrumenter.py`:

```python
class TestLineCapture:
    def test_events_carry_solution_relative_line(self):
        code = wrap_traced_solution(BUBBLE_SORT, "bubble_sort")
        events = parse_trace(_run(code, json.dumps({"values": [5, 1, 4, 2, 8]})))
        # BUBBLE_SORT's `__trace("pointer", ...)` is on line 6 of the solution.
        pointer = next(e for e in events if e.kind == "pointer")
        assert pointer.line == 6
        # `__trace("init", ...)` is on line 2.
        assert events[0].line == 2

    def test_offset_is_stable_across_functions(self):
        code = wrap_traced_solution(LINEAR_SEARCH, "linear_search")
        events = parse_trace(_run(code, json.dumps({"values": [4, 2, 7, 1], "target": 7})))
        compare = next(e for e in events if e.kind == "compare")
        assert compare.line == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/unit/test_trace_instrumenter.py::TestLineCapture -p no:cacheprovider --no-cov -q`
Expected: FAIL — `pointer.line` is None (no capture yet).

- [ ] **Step 3: Write minimal implementation**

In `backend/app/services/trace_instrumenter.py`, replace `_TRACE_HELPER` with a template that carries the offset placeholder and a runtime guard:

```python
_TRACE_HELPER_TEMPLATE = """\
import json as __json
import sys as __sys

__TRACE = []
__CODE_OFFSET = 0


def __trace(event, **fields):
    __frame = __sys._getframe(1) if hasattr(__sys, "_getframe") else None
    if __frame is not None and "line" not in fields:
        fields["line"] = __frame.f_lineno - __CODE_OFFSET
    __TRACE.append({"event": event, **fields})
"""


def _build_helper() -> str:
    """Finalize the helper, injecting the wrapped-file line offset.

    The placeholder line keeps the template's line count stable, so the offset
    computed here stays correct after substitution.
    """
    offset = _TRACE_HELPER_TEMPLATE.count("\n") + 1
    return _TRACE_HELPER_TEMPLATE.replace(
        "__CODE_OFFSET = 0", f"__CODE_OFFSET = {offset}"
    )
```

In `wrap_traced_solution`, use the built helper:

```python
    helper = _build_helper()
    return f"{helper}\n{code}\n\n{wrapper}".strip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/unit/test_trace_instrumenter.py -p no:cacheprovider --no-cov -q`
Expected: PASS (existing wrapper tests plus `TestLineCapture`).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/trace_instrumenter.py backend/tests/unit/test_trace_instrumenter.py
git commit -m "feat(animation): capture caller line in the trace helper (#240)"
```

---

### Task F3: Display code and line map

**Files:**
- Modify: `backend/app/services/trace_instrumenter.py`
- Test: `backend/tests/unit/test_trace_instrumenter.py`

**Interfaces:**
- Produces: `display_code_and_map(code: str) -> tuple[str, dict[int, int]]` — display code with standalone `__trace(...)` statements removed, and a map from original line → display line.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_trace_instrumenter.py`:

```python
from app.services.trace_instrumenter import display_code_and_map

TRACE_DISPLAY_SAMPLE = """\
def total(values):
    __trace("init", values=values, family="array")
    acc = 0
    for i, v in enumerate(values):
        __trace("pointer", name="i", index=i)
        acc += v
        __trace("mark", i=i, state="seen")
    return acc
"""


class TestDisplayCodeAndMap:
    def test_strips_standalone_trace_calls(self):
        display, _ = display_code_and_map(TRACE_DISPLAY_SAMPLE)
        assert "__trace" not in display
        assert "acc += v" in display
        assert "return acc" in display

    def test_maps_trace_lines_to_preceding_statement(self):
        _, mapping = display_code_and_map(TRACE_DISPLAY_SAMPLE)
        # pointer's __trace is line 5 -> the `for` header (display line 3)
        assert mapping[5] == 3
        # mark's __trace is line 7 -> `acc += v` (display line 4)
        assert mapping[7] == 4

    def test_init_with_no_preceding_statement_maps_forward(self):
        display, mapping = display_code_and_map(
            'def f(x):\n    __trace("init", x=x)\n    return x\n'
        )
        assert mapping[2] == 1  # def f(x):
        assert "return x" in display

    def test_non_statement_trace_call_is_kept(self):
        code = 'def f(x):\n    y = __trace("init", x=x)\n    return y\n'
        display, mapping = display_code_and_map(code)
        assert "__trace" in display
        assert mapping[2] == 2

    def test_syntax_error_returns_identity_map(self):
        bad = "def f(:\n    pass\n"
        display, mapping = display_code_and_map(bad)
        assert display == bad
        assert mapping == {1: 1, 2: 2}

    def test_multiline_trace_call_is_fully_stripped(self):
        code = (
            "def f(x):\n"
            "    __trace(\n"
            '        "init",\n'
            "        x=x,\n"
            "    )\n"
            "    return x\n"
        )
        display, mapping = display_code_and_map(code)
        assert "__trace" not in display
        assert display == "def f(x):\n    return x"
        # Every original line of the call maps to the def line (display 1).
        assert mapping[2] == mapping[3] == mapping[4] == mapping[5] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/unit/test_trace_instrumenter.py::TestDisplayCodeAndMap -p no:cacheprovider --no-cov -q`
Expected: FAIL — `ImportError: cannot import name 'display_code_and_map'`.

- [ ] **Step 3: Write minimal implementation**

Add to `backend/app/services/trace_instrumenter.py` (top: `import ast`):

```python
def _is_trace_statement(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "__trace"
    )


def display_code_and_map(code: str) -> tuple[str, dict[int, int]]:
    """Strip standalone ``__trace(...)`` statements; map original→display line.

    Each stripped line maps to the nearest preceding kept line, falling back to
    the nearest following kept line when there is none. Syntactically invalid
    code is returned unchanged with an identity map.
    """
    lines = code.splitlines()
    identity = {i: i for i in range(1, len(lines) + 1)}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code, identity

    removed: set[int] = set()
    for node in ast.walk(tree):
        if _is_trace_statement(node):
            end = getattr(node, "end_lineno", None) or node.lineno
            removed.update(range(node.lineno, end + 1))

    kept = [i for i in range(1, len(lines) + 1) if i not in removed]
    display_pos = {orig: idx + 1 for idx, orig in enumerate(kept)}
    mapping: dict[int, int] = {}
    for orig in range(1, len(lines) + 1):
        if orig in display_pos:
            mapping[orig] = display_pos[orig]
            continue
        prev = max((k for k in kept if k < orig), default=None)
        if prev is not None:
            mapping[orig] = display_pos[prev]
        else:
            nxt = min((k for k in kept if k > orig), default=None)
            if nxt is not None:
                mapping[orig] = display_pos[nxt]

    display_code = "\n".join(lines[i - 1] for i in kept)
    return display_code, mapping
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/unit/test_trace_instrumenter.py -p no:cacheprovider --no-cov -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/trace_instrumenter.py backend/tests/unit/test_trace_instrumenter.py
git commit -m "feat(animation): derive display code and line map (#240)"
```

---

### Task F4: Beat-IR fields on AnimationStepSpec

**Files:**
- Modify: `backend/app/models/animation_spec.py`
- Test: `backend/tests/unit/test_animation_spec.py` (create)

**Interfaces:**
- Produces: `AnimationStepSpec.line: Optional[int]`, `.annotation: Optional[str]`, `.role: Optional[Literal["intro","loop","climax","outro"]]`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_animation_spec.py`:

```python
"""Unit tests for the semantic animation IR additions (#240)."""

import pytest
from pydantic import ValidationError

from app.models.animation_spec import AnimationStepSpec


class TestAnimationStepSpecFields:
    def test_new_fields_default_to_none(self):
        step = AnimationStepSpec(action="compare")
        assert step.line is None
        assert step.annotation is None
        assert step.role is None

    def test_accepts_line_annotation_and_role(self):
        step = AnimationStepSpec(
            action="found", index=3, line=42, annotation="target found", role="climax"
        )
        assert step.line == 42
        assert step.annotation == "target found"
        assert step.role == "climax"

    def test_rejects_non_positive_line(self):
        with pytest.raises(ValidationError):
            AnimationStepSpec(action="compare", line=0)

    def test_rejects_unknown_role(self):
        with pytest.raises(ValidationError):
            AnimationStepSpec(action="compare", role="middle")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/unit/test_animation_spec.py -p no:cacheprovider --no-cov -q`
Expected: FAIL — `TypeError: unexpected keyword argument 'line'` / defaults missing.

- [ ] **Step 3: Write minimal implementation**

In `backend/app/models/animation_spec.py`, add to `AnimationStepSpec` after `label`:

```python
    line: Optional[int] = Field(
        None, ge=1, description="1-based source line in the canonical solution"
    )
    annotation: Optional[str] = Field(
        None, max_length=200, description="Causal callout text for the beat"
    )
    role: Optional[Literal["intro", "loop", "climax", "outro"]] = Field(
        None, description="Pacing role, consumed and stripped by the planner"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/unit/test_animation_spec.py -p no:cacheprovider --no-cov -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/animation_spec.py backend/tests/unit/test_animation_spec.py
git commit -m "feat(animation): add line/annotation/role to the step IR (#240)"
```

---

### Task F5: Pacing interface

**Files:**
- Create: `backend/app/services/animation_pacing.py`
- Test: `backend/tests/unit/test_animation_pacing.py` (create)

**Interfaces:**
- Produces: `PacingProfile`, `DEFAULT_PROFILE`, `apply_pacing(beats, profile=DEFAULT_PROFILE) -> list[dict]`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_animation_pacing.py`:

```python
"""Unit tests for role-aware beat pacing (#240)."""

from app.services.animation_pacing import PacingProfile, apply_pacing


def _beat(role=None, duration=0.3):
    beat = {"narration": "x", "motion": [{"target": "a", "op": "move", "duration": duration}]}
    if role is not None:
        beat["role"] = role
    return beat


class TestApplyPacing:
    def test_rewrites_duration_by_role_and_strips_role(self):
        beats = apply_pacing([_beat(role="climax")])
        assert beats[0]["motion"][0]["duration"] == 0.5
        assert "role" not in beats[0]

    def test_beat_without_role_is_unchanged(self):
        beats = apply_pacing([_beat()])
        assert beats[0]["motion"][0]["duration"] == 0.3
        assert "role" not in beats[0]

    def test_duration_is_clamped_to_validator_window(self):
        loud = PacingProfile(intro=0.0, loop=0.4, climax=9.0, outro=0.3)
        beats = apply_pacing([_beat(role="intro"), _beat(role="climax")], loud)
        assert beats[0]["motion"][0]["duration"] == 0.1
        assert beats[1]["motion"][0]["duration"] == 5.0

    def test_tolerates_non_list_input(self):
        assert apply_pacing(None) is None
        assert apply_pacing([]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/unit/test_animation_pacing.py -p no:cacheprovider --no-cov -q`
Expected: FAIL — `ModuleNotFoundError: app.services.animation_pacing`.

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/services/animation_pacing.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/unit/test_animation_pacing.py -p no:cacheprovider --no-cov -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/animation_pacing.py backend/tests/unit/test_animation_pacing.py
git commit -m "feat(animation): add role-aware pacing interface (#240)"
```

---

### Task F6: Visual metaphor registry (data only)

**Files:**
- Create: `backend/app/services/visual_metaphors.py`
- Test: `backend/tests/unit/test_visual_metaphors.py` (create)

**Interfaces:**
- Produces: `VisualMetaphor`, `metaphor_for(family) -> Optional[VisualMetaphor]`; colors mirror `family_compilers` constants.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/unit/test_visual_metaphors.py`:

```python
"""Unit tests for the visual metaphor registry (#240).

The registry must mirror the compiler's current palette exactly so workstream D
can flip family_compilers onto it with zero rendered-output change.
"""

import pytest

from app.services import family_compilers as fc
from app.services.visual_metaphors import metaphor_for

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/unit/test_visual_metaphors.py -p no:cacheprovider --no-cov -q`
Expected: FAIL — `ModuleNotFoundError: app.services.visual_metaphors`.

- [ ] **Step 3: Write minimal implementation**

Create `backend/app/services/visual_metaphors.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/unit/test_visual_metaphors.py -p no:cacheprovider --no-cov -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/visual_metaphors.py backend/tests/unit/test_visual_metaphors.py
git commit -m "feat(animation): add visual metaphor registry data (#240)"
```

---

### Task F7: Validator tolerates the additive beat keys

**Files:**
- Test: `backend/tests/unit/test_animation_validator.py`

**Interfaces:**
- Consumes: `AnimationValidator.validate`.
- Produces: proof that `code_line`/`annotation`/`role` on a beat do not break validation.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/unit/test_animation_validator.py` (match its existing helper style; if it has no shared `_scene` helper, build the minimal valid script inline):

```python
class TestAdditiveBeatKeys:
    def test_extra_beat_keys_do_not_break_validation(self):
        script = {
            "steps": [
                {
                    "narration": "start",
                    "shapes": [
                        {"id": "a", "type": "rect", "x": 0, "y": 0, "width": 10, "height": 10},
                        {"id": "b", "type": "rect", "x": 20, "y": 0, "width": 10, "height": 10},
                    ],
                    "motion": [
                        {"target": "a", "op": "appear", "duration": 0.3},
                        {"target": "b", "op": "appear", "duration": 0.3},
                    ],
                    "code_line": 2,
                },
                {
                    "narration": "move",
                    "shapes": [],
                    "motion": [{"target": "a", "op": "move", "to": [20, 0], "duration": 0.3}],
                    "code_line": 3,
                    "annotation": {"text": "why"},
                    "role": "climax",
                },
                {
                    "narration": "done",
                    "shapes": [],
                    "motion": [{"target": "a", "op": "fill", "to": "#22c55e", "duration": 0.3}],
                    "code_line": 4,
                    "badge": {"time": "O(n)", "space": "O(1)"},
                },
            ]
        }
        validated, reason = AnimationValidator().validate(script)
        assert validated is not None, reason
        assert validated["steps"][1]["code_line"] == 3
```

- [ ] **Step 2: Run test to verify it fails (or confirms current behaviour)**

Run: `cd backend && python3 -m pytest tests/unit/test_animation_validator.py::TestAdditiveBeatKeys -p no:cacheprovider --no-cov -q`
Expected: PASS if the validator already ignores unknown keys; if it FAILS, the validator is reading keys it should not and Step 3 is required.

- [ ] **Step 3: Implement only if Step 2 failed**

If validation rejected the script, narrow the offending check in
`backend/app/services/animation_validator.py` to the documented keys
(`narration`/`shapes`/`motion`/`camera`/`badge`) rather than iterating all step
keys. Do not add whitelisting that would reject the new keys.

- [ ] **Step 4: Run the full animation unit suite**

Run: `cd backend && python3 -m pytest tests/unit -p no:cacheprovider --no-cov -q`
Expected: PASS (whole unit tier green).

- [ ] **Step 5: Commit**

```bash
git add backend/tests/unit/test_animation_validator.py backend/app/services/animation_validator.py
git commit -m "test(animation): pin additive beat keys against the validator (#240)"
```

---

### Task F8: Gate check — canonical animations still green

**Files:**
- Test: `backend/tests/integration/test_animation_coverage.py` (existing)

- [ ] **Step 1: Run the animation coverage integration test**

Run: `cd backend && python3 -m pytest tests/integration/test_animation_coverage.py -p no:cacheprovider --no-cov -q`
Expected: PASS if a PostgreSQL branch DB and Piston are reachable; otherwise record the skip reason and note it in the PR (do not weaken the test).

- [ ] **Step 2: Lint + format**

Run: `cd backend && ruff check . && ruff format . --check`
Expected: clean.

- [ ] **Step 3: Push the branch and open the PR**

```bash
git push -u origin feat/240-animation-ir-foundation
gh pr create --title "feat(animation): deterministic pedagogy IR foundation (#240)" \
  --body "Shared contracts for #284/#285/#286/#287. Spec: docs/superpowers/specs/2026-09-23-animation-deterministic-pedagogy-design.md"
```
