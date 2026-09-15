# A2 Pedagogy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich planner narrations (values + why), guarantee camera + final badge, eliminate duplicate narrations.

**Architecture:** Edit `backend/app/services/scene_planner.py` only (`plan_array` + shared beat post-processing). No dispatcher signature change, no validator cap change.

**Tech Stack:** Python, FastAPI service layer, pytest.

**Spec:** `docs/superpowers/specs/2026-09-15-animation-quality-design.md` (§3 A2)

## Global Constraints

- `plan(spec) -> beats` signature frozen; `AnimationStepSpec` schema untouched.
- Narrations ≤ 300 chars; beats ≥ 3; validator caps unchanged.
- TDD red → green → refactor; `ruff check .`, `ruff format . --check`, `python -m pytest tests/unit` green.
- Never read student code; optimal-solution trace only.

---

### Task 1: Value-rich narrations for plan_array

**Files:**
- Modify: `backend/app/services/scene_planner.py:319-482`
- Test: `backend/tests/unit/test_scene_planner_narration.py` (new)

**Interfaces:**
- Consumes: `AlgorithmAnimation` (initialState.array, steps with indices/values).
- Produces: narration strings containing values and positions.

- [ ] **Step 1: Write the failing test**

```python
from app.models.animation_spec import (
    AlgorithmAnimation, AnimationStepSpec, Complexity, InitialState,
)
from app.services import scene_planner


def _spec():
    return AlgorithmAnimation(
        algorithm="bubble_sort",
        visualization="bars",
        initialState=InitialState(array=[5, 1, 4], extra={}),
        steps=[
            AnimationStepSpec(action="compare", indices=[0, 1]),
            AnimationStepSpec(action="swap", indices=[0, 1]),
            AnimationStepSpec(action="write", index=0, values=[1]),
        ],
        complexity=Complexity(time="O(n²)", space="O(1)"),
        title="Bubble Sort",
    )


def test_compare_narration_includes_values():
    beats = scene_planner.plan_array(_spec())
    assert "5" in beats[1]["narration"] and "1" in beats[1]["narration"]


def test_swap_narration_includes_indices_and_values():
    beats = scene_planner.plan_array(_spec())
    assert "[0]" in beats[2]["narration"] and "[1]" in beats[2]["narration"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_scene_planner_narration.py -v`
Expected: FAIL with `assert "5" in 'Compare [0, 1]'` (current terse narration)

- [ ] **Step 3: Write minimal implementation**

In `plan_array`, replace:
`narr = f"Compare {idxs}"` with value lookup from `display`:
```python
vals = [str(display[i])[:12] if 0 <= i < n else "?" for i in idxs[:2]]
narr = f"Compare [{idxs[0]}]={vals[0]} vs [{idxs[1]}]={vals[1] if len(vals) > 1 else '?'}"
```
Swap: `narr = f"Swap [{a}]={display[a]} ↔ [{b}]={display[b]}"` (guard bounds).
Write/window/mark/pointer: same pattern, always `[:300]` truncated (already done).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_scene_planner_narration.py tests/unit/test_family_compilers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scene_planner.py backend/tests/unit/test_scene_planner_narration.py
git commit -m "feat(162): enrich array planner narrations"
```

### Task 2: Camera + badge guarantees and dedupe

**Files:**
- Modify: `backend/app/services/scene_planner.py` (`plan_array`, shared tail)
- Test: extend `backend/tests/unit/test_scene_planner_narration.py`

**Interfaces:**
- Consumes: beats from Task 1.
- Produces: every focus beat has `camera`; final beat has `badge`; no duplicate consecutive narrations.

- [ ] **Step 1: Write the failing test**

```python
def test_every_focus_beat_has_camera_and_final_has_badge():
    beats = scene_planner.plan_array(_spec())
    assert beats[0].get("camera", {}).get("action") == "reset"
    assert beats[-1].get("badge") == {"time": "O(n²)", "space": "O(1)"}


def test_no_duplicate_consecutive_narrations():
    spec = _spec()
    spec.steps = [
        AnimationStepSpec(action="compare", indices=[0, 1]),
        AnimationStepSpec(action="compare", indices=[0, 1]),
        AnimationStepSpec(action="compare", indices=[0, 1]),
    ]
    beats = scene_planner.plan_array(spec)
    narrs = [b["narration"] for b in beats[1:-1]]
    assert len(set(narrs)) == len(narrs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_scene_planner_narration.py -v`
Expected: FAIL on duplicate narrations (three identical `"Compare …"` beats)

- [ ] **Step 3: Write minimal implementation**

After building `beats` in `plan_array`, add post-pass:
```python
seen_prev = None
for b in beats[1:-1]:
    if b["narration"] == seen_prev:
        b["narration"] = (b["narration"] + " (cont.)")[:300]
    seen_prev = b["narration"]
```
Verify intro already has `camera.reset` and tail already has `badge` (both exist); add only if missing — do not duplicate.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_scene_planner_narration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scene_planner.py backend/tests/unit/test_scene_planner_narration.py
git commit -m "feat(162): guarantee camera badge and dedupe narrations"
```

### Task 3: Verify

- [ ] Run `ruff check backend/app/services/scene_planner.py`, `ruff format --check backend/app/services/scene_planner.py`, `python -m pytest tests/unit -q` — all green.
- [ ] Run `python scripts/animate_coverage.py` (or fake-executor corpus) and confirm zero `lint_quality` warnings on array family.
