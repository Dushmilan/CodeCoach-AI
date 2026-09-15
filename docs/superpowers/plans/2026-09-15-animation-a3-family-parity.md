# A3 Family Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace placeholder rects with real layouts for tree/graph/grid/stack/intervals/linked_list/backtrack, reusing design tokens.

**Architecture:** Extract shared `_tree_layout` into `scene_planner`, have `family_compilers` import it; upgrade per-family `plan_*` helpers with real coordinates; tokens additive-only.

**Tech Stack:** Python, pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-animation-quality-design.md` (§3 A3)

## Global Constraints

- `plan(spec)` dispatcher signature frozen; per-family `(spec) -> beats` shape kept.
- All x in ±960, y in ±540; beats ≥ 3; camera on intro; badge on final.
- No renames of existing token keys; new keys additive.
- TDD; `ruff check .`, `ruff format . --check`, `python -m pytest tests/unit` green.

---

### Task 1: Shared tree layout helper (no duplication)

**Files:**
- Modify: `backend/app/services/scene_planner.py` (add `_tree_layout` + positions)
- Modify: `backend/app/services/family_compilers.py` (import shared helper, delete local copy)
- Test: `backend/tests/unit/test_tree_layout_shared.py` (new)

**Interfaces:**
- Consumes: `n` (node count).
- Produces: `scene_planner.tree_layout(n) -> [{x, y}]` used by both modules.

- [ ] **Step 1: Write the failing test**

```python
from app.services import scene_planner


def test_tree_layout_matches_compiler_math():
    pos = scene_planner.tree_layout(3)
    assert len(pos) == 3
    assert pos[0]["y"] < pos[1]["y"]  # root above children
    assert pos[1]["x"] < pos[2]["x"]  # left before right
    assert all(abs(p["x"]) <= 960 and abs(p["y"]) <= 540 for p in pos)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_tree_layout_shared.py -v`
Expected: FAIL with "has no attribute 'tree_layout'"

- [ ] **Step 3: Write minimal implementation**

Copy `_tree_layout` math from `family_compilers.py:545-555` into `scene_planner.py` as public `tree_layout(n)` (same `TREE_WIDTH 620`, `TREE_TOP -240`, `TREE_LEVEL_H 96`), then in `family_compilers.py` replace local `_tree_layout` body with `from app.services.scene_planner import tree_layout as _tree_layout` (keep name, delete duplicate math). Keep `plan_tree` behavior identical this task.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_tree_layout_shared.py tests/unit/test_family_compilers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scene_planner.py backend/app/services/family_compilers.py backend/tests/unit/test_tree_layout_shared.py
git commit -m "refactor(162): share tree layout helper"
```

### Task 2: Real planner layouts with golden tests

**Files:**
- Modify: `backend/app/services/scene_planner.py` (`plan_tree`, `plan_graph`, `plan_stack`, `plan_intervals`, `plan_linked_list`, `plan_backtrack`)
- Modify: `backend/app/services/animation_design_tokens.py` (additive keys only if needed)
- Test: `backend/tests/unit/test_family_layout_parity.py` (new)

**Interfaces:**
- Consumes: `tree_layout` from Task 1; `tokens.PALETTE/DURATION/CAMERA`.
- Produces: beats with real coordinates per family.

- [ ] **Step 1: Write the failing test**

```python
from app.models.animation_spec import (
    AlgorithmAnimation, AnimationStepSpec, Complexity, InitialState,
)
from app.services import scene_planner


def _beats(viz, steps):
    spec = AlgorithmAnimation(
        algorithm="x", visualization=viz,
        initialState=InitialState(array=[1, 2, 3], extra={}),
        steps=[AnimationStepSpec(action=a) for a in steps],
        complexity=Complexity(time="O(n)", space="O(1)"), title="T",
    )
    return scene_planner.plan(spec)


def test_tree_beats_use_level_layout_and_camera_badge():
    beats = _beats("tree", ["visit", "choose", "backtrack"])
    assert len(beats) >= 3
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") is not None
    xs = [s["x"] for b in beats for s in b["shapes"] if "x" in s]
    assert len(set(xs)) > 1  # not all stacked at same x


def test_graph_beats_spread_nodes():
    beats = _beats("graph", ["visit", "edge", "visit"])
    xs = [s["x"] for b in beats for s in b["shapes"] if "x" in s]
    assert len(set(xs)) > 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_family_layout_parity.py -v`
Expected: FAIL (tree nodes share placeholder x grid / missing spread)

- [ ] **Step 3: Write minimal implementation**

`plan_tree`: use `tree_layout(max_idx+1)` for node positions + `line` edge shapes from parent to child (mirror `_compile_tree` math). `plan_graph`: circular positions radius 230 (`GRAPH_RADIUS`), same angle math as `_compile_graph`. `plan_stack`: keep box + vertical item offsets (already real — just ensure distinct y per depth). Others: keep existing but ensure distinct coordinates per index (no two shapes share identical x,y unless intended). No token renames.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_family_layout_parity.py tests/unit/test_family_compilers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scene_planner.py backend/app/services/animation_design_tokens.py backend/tests/unit/test_family_layout_parity.py
git commit -m "feat(162): real family layouts in planner"
```

### Task 3: Verify

- [ ] Run `ruff check .`, `ruff format . --check`, `python -m pytest tests/unit -q` — green.
- [ ] Bounds audit: assert every shape x/y in golden beats within ±960/±540.
