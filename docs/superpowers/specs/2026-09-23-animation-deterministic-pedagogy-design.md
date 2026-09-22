# Animation Deterministic Pedagogy — Design Spec

- **Date:** 2026-09-23
- **Status:** Draft — awaiting human review
- **Tracker:** #240 (Reel-quality shot logic + pedagogy)
- **Sub-issues:** #284 (A · dual-pane code sync), #285 (C · adaptive pacing), #286 (D · visual metaphor registry), #287 (B · causal annotations)
- **Foundation branch:** `feat/240-animation-ir-foundation`

## 1. Context

Tracker #240 keeps animation quality open until the visuals actually teach. A
design review proposed four upgrades: a verified solution registry, a visual
metaphor registry, dual-pane code↔visual sync, causal annotations, and adaptive
pacing. This spec records what is already true, what is genuinely missing, and
the shared contracts that let the missing work proceed in parallel without
merge chaos.

### 1.1 Already true (verified against `main` `687e62a`)

- The canonical animation path is **already LLM-free**:
  `SolutionAnimationService.build_animation`
  (`backend/app/services/solution_animation_service.py:325`) →
  `resolve_algorithm` / `get_reference_solution` → `wrap_traced_solution` →
  Piston → `parse_trace` → `scene_planner.plan()` / `compile_family()` →
  `AnimationValidator.validate()`. Groq is firewalled to chat.
- `reference_solutions.py` **already is** the verified solution registry: 103
  curated optimal solutions with `family/title/function/signature/primary/match_keys/code`
  (`backend/app/services/reference_solutions.py:29`).
- Visuals are already deterministic and compiler-owned
  (`family_compilers.py:1-12`, `scene_planner.py:1-10`).
- Tracker defect 1 (stateless rendering) is **shipped**: cumulative scene state
  in `frontend/src/components/visualization/GenericSceneRenderer.tsx:221-253`
  (#281).

### 1.2 Genuinely missing

| Workstream | Gap |
|---|---|
| A · dual-pane code sync | Beats carry no source line; the trace carries no line; the canonical script exposes no code to highlight. |
| B · causal annotations | No intent data in the trace; no annotation primitive in the beat IR. |
| C · adaptive pacing | Durations are near-uniform; no role-aware pacing. |
| D · metaphor registry | Visual vocabulary is hardcoded in `family_compilers.py`, not data. |

## 2. Non-goals

- **No DB/YAML migration of `reference_solutions.py`.** It is already the
  verified registry; a storage move is an admin-UX decision with no correctness
  benefit (AGENTS.md "no speculative work"). Revisit only with a concrete need.
- **No LLM in the canonical path.** It stays deterministic.
- **No new shape or motion primitive** unless a workstream proves the existing
  five shapes / eight ops cannot express it.
- **No behaviour change from the foundation itself** — additive contracts only.

## 3. Shared contracts (foundation)

All contracts are **additive** and land before the four workstreams. The
validator ignores unknown *step-level* keys, so no validator change is required
for them.

### 3.1 Trace line capture (A, B)

`trace_instrumenter.py` defines the `__trace` helper injected ahead of the
canonical solution. Add caller-line capture:

```python
def __trace(event, **fields):
    __TRACE.append(
        {"event": event, "line": __sys._getframe(1).f_lineno - __CODE_OFFSET, **fields}
    )
```

`__CODE_OFFSET` is the number of wrapped-file lines before the canonical
solution's own line 1. Because the offset line itself occupies a line, it is
computed from a placeholder and then substituted (same line count, so the offset
stays correct). The template stays immutable; the finalized helper is built
locally per call, never by mutating a module global:

```python
def _build_helper() -> str:
    helper = _TRACE_HELPER_TEMPLATE  # contains the placeholder line `__CODE_OFFSET = 0`
    offset = helper.count("\n") + 1  # helper lines + the f-string's blank line
    return helper.replace("__CODE_OFFSET = 0", f"__CODE_OFFSET = {offset}")
```

Derivation: `wrap_traced_solution` returns `f"{helper}\n{code}\n\n{wrapper}"`.
The solution's line 1 sits after every helper line plus the one `\n` the f-string
adds, so `offset = helper.count("\n") + 1`. A foundation test asserts the observed
`f_lineno` of a known call minus `__CODE_OFFSET` equals its 1-based line inside
`entry["code"]`.

`sys._getframe` is CPython-specific, which is the documented runtime (Piston runs
CPython); `__trace` records `line` only when the attribute is available, so a
non-CPython runtime degrades to no line rather than crashing the trace.

This yields **1-based line numbers relative to `entry["code"]`**, independent of
the wrapper. `trace_parser.TraceEvent` gains an optional `line`; a non-int or
non-positive `line` is dropped, never coerced.

### 3.2 Display code + line map (A)

Canonical solutions interleave `__trace(...)` statements with the real logic.
Displaying them verbatim leaks the instrumentation harness and undercuts the
pedagogy. Add a pure helper to `trace_instrumenter.py`:

```python
def display_code_and_map(code: str) -> tuple[str, dict[int, int]]:
    """Strip standalone __trace(...) statements; map original→display line.

    Each stripped line maps to the nearest preceding kept line, falling back
    to the nearest following kept line when there is no preceding one.
    """
```

Detection uses `ast`: an `Expr` statement whose value is a `Call` to the name
`__trace`. This is robust to formatting and multi-line calls; every original line
covered by a stripped statement's span (from its `lineno` to `end_lineno`) is
mapped, not just the first. Mapping rule is deliberate and matches the catalog
convention (`stack.append(ch)` immediately followed by `__trace("push", ...)`), so
`push` highlights the `append` line.

`display_code_and_map` is a foundation deliverable with its own tests, so A only
wires it.

### 3.3 Beat IR additions (A, B, C)

`AnimationStepSpec` (`backend/app/models/animation_spec.py`) gains three optional
fields:

```python
line: Optional[int] = None        # 1-based line in entry["code"]
annotation: Optional[str] = None  # causal callout text (B)
role: Optional[Literal["intro", "loop", "climax", "outro"]] = None  # pacing (C)
```

The semantic `annotation` is the callout **text**; the planner wraps it into the
beat's `annotation` object (`{"text": str}`) so the renderer can gain
anchor/placement fields later without another schema change.

Beat IR (the plain dicts planners emit) gains optional keys, tolerated by
`AnimationValidator` because it only reads `narration`/`shapes`/`motion`/`camera`/
`badge`:

```python
{"narration": str, "shapes": [...], "motion": [...],
 "code_line": int | None,     # display-code line (A)
 "annotation": dict | None,   # {"text": str} rendered as a callout (B)
 "camera": {...}, "badge": {...}}
```

`code_line`/`annotation`/`role` are **transient** during planning: `role` is
stripped by pacing before output; `code_line` and `annotation` survive into the
validated script.

### 3.4 Pacing interface (C)

New `backend/app/services/animation_pacing.py`:

```python
@dataclass(frozen=True)
class PacingProfile:
    intro: float
    loop: float
    climax: float
    outro: float

DEFAULT_PROFILE = PacingProfile(intro=0.25, loop=0.35, climax=0.5, outro=0.25)

def apply_pacing(beats: list[dict], profile: PacingProfile = DEFAULT_PROFILE) -> list[dict]:
    """Rewrite each beat's motion durations by its `role`, then strip `role`.

    Beats without a role keep their durations (no behaviour change). Every
    rewritten duration is clamped to the validator's 0.1-5.0s window.
    """
```

Called from `scene_planner._finalize_beats`. The foundation ships the module and
the no-role default; C adds role tagging in the planners and tunes the profile.

### 3.5 Metaphor registry interface (D)

New `backend/app/services/visual_metaphors.py`:

```python
@dataclass(frozen=True)
class VisualMetaphor:
    family: str
    metaphor: str          # "plates", "lockers", "roots_and_branches", ...
    base_shape: str        # rect | ellipse | polygon
    layout: str            # vertical_stack | grid_2x5 | reingold_tilford | ...
    colors: dict[str, str] # semantic → #rrggbb, values copied from current palette
    motion_profile: dict[str, dict]

def metaphor_for(family: str) -> VisualMetaphor | None: ...
```

Foundation ships the module with values that **exactly mirror today's
`family_compilers` palette/layout**, plus a test asserting parity. D then makes
`family_compilers` consume it with zero rendered-output change.

## 4. Workstream A — dual-pane code↔visual sync (#284)

**Goal:** every action beat highlights the canonical-solution line it
choreographs, beside the scene.

- `_try_planner` sets `line=e.line` on each `AnimationStepSpec` it builds from an
  event; `scene_planner.plan` copies `step.line` → `beat["code_line"]`.
- Binary-search steps synthesized by `_translate_search_events` carry no trace
  line, so those beats have `code_line: null` (honest, never invented).
- After planning, `build_animation` maps each beat's original `code_line` through
  `line_map` from `display_code_and_map`, and adds `"animated_code": display_code`
  to the returned script.
- Frontend: new `CodePane.tsx` rendered by `AnimationScriptRenderer` beside the
  visualizer, highlighting `step.code_line`; `AnimationStep.code_line` added to
  `types/index.ts`.
- Fallback compiler path (`compile_family`) leaves `code_line` null for now —
  keeps A disjoint from D's `family_compilers.py`.

**Files owned:** `trace_instrumenter.py` (wiring only), `trace_parser.py`,
`solution_animation_service.py`, `scene_planner.py` (`plan`/`_try_planner`
line plumbing), new `frontend/src/components/visualization/CodePane.tsx`,
`AnimationScriptRenderer.tsx`, `types/index.ts`.

## 5. Workstream B — causal annotations (#287)

**Goal:** a floating "math bubble" explaining each decision, e.g.
`"sum 15 > target 9 → move right pointer left"`.

Depends on A (line plumbing) and on real intent data.

- Extend `__trace` with an `intent` field; reference solutions emit the reason at
  the branch they take (e.g. `__trace("pointer", name="right", index=r, intent="sum_too_large")`).
- Planner turns a step with `annotation` into an annotation beat: a background
  `rect` + `text` shape that `appear`s, holds, and `disappear`s. Because the
  validator requires a transform op on every non-intro beat, the annotation beat
  also carries a `label` op on its text (a transform), or rides the decision
  beat's existing transform.
- No fake causality: annotations appear only where the reference solution emits
  `intent`.

**Files owned:** `reference_solutions.py` (intent emission), `scene_planner.py`
(annotation beats), new `frontend/src/components/visualization/AnnotationOverlay.tsx`
(or a branch inside `GenericSceneRenderer`), `animation_spec.py` consumers.

## 6. Workstream C — adaptive pacing (#285)

**Goal:** cinematic weight — fast setup, rhythmic loop, slow "Aha!" climax, snap
return.

- Planners tag each beat with `role`: intro (first), loop (default), climax
  (`found` / base case / final `return`), outro (badge beat).
- `_finalize_beats` calls `apply_pacing`, which rewrites durations within the
  validator's 0.1–5.0s window and strips `role`.
- `AnimationPlayer` already auto-advances on the longest motion per beat
  (`AnimationPlayer.tsx:52-80`) — no frontend change.

**Files owned:** new `animation_pacing.py`, `scene_planner.py` (`_finalize_beats`
+ role tagging).

## 7. Workstream D — visual metaphor registry (#286)

**Goal:** formalize the compiler's visual vocabulary as data.

- `family_compilers.py` reads palette/layout/motion from `metaphor_for(family)`
  instead of module constants.
- Pure extraction: a golden test pins identical beats before/after for one
  algorithm per family.

**Files owned:** new `visual_metaphors.py`, `family_compilers.py`.

## 8. Cross-cutting: validation & gates

- `AnimationValidator` stays the structural gate; new beat keys are additive.
- The `ANIMATION` use case (`backend/app/use_cases/question_validation/animation.py`)
  must stay green for all 103 canonical solutions after every workstream.
- `animation.steps >= 3` is unchanged.
- No API contract break: `data`/`steps` remain; `animated_code` is added (already
  present on the frontend `AnimationScript` type).

## 9. Testing strategy

- **Foundation:** parser line field; instrumenter offset math; `display_code_and_map`
  mapping on `bubble_sort`/`valid_parentheses`; schema round-trip for the three
  new `AnimationStepSpec` fields; `apply_pacing` no-op when roles absent; metaphor
  palette parity with `family_compilers`.
- **A:** beat `code_line` present and in range for a planner-run algorithm;
  service payload carries `animated_code`; Vitest `CodePane` highlight.
- **B:** intent emission → annotation beat appears/disappears; validator green.
- **C:** climax beat duration > loop beat duration; validator green.
- **D:** golden beats unchanged.
- **Browser (AGENTS.md gate):** each workstream records desktop (1280×800) +
  mobile (390×844) screenshots of the affected journey, read back through vision.

## 10. Rollout / parallelization

1. **Foundation** (this branch): contracts + tests + this spec → PR into `main`.
2. **Parallel:** A (#284), C (#285), D (#286) in their own worktrees off the
   foundation commit; disjoint file ownership per §4–§7.
3. **Then:** B (#287), which reuses A's line plumbing.
4. Integration: each workstream PR is reviewed and merged in order; conflicts are
   resolved by the integrator, not by shared worktrees.

## 11. Risks

- **Line offset drift** if the wrapper changes — pinned by a foundation test on
  the exact offset computation.
- **`__trace` line mapping** is a heuristic for events that precede their
  statement (e.g. `visit`); tests pin the accepted mapping and it is documented.
- **Merge conflicts** on `scene_planner.py` between A and C — mitigated by
  confining A to `plan`/`_try_planner` plumbing and C to `_finalize_beats`.
- **Pacing overrides** must stay within 0.1–5.0s or the validator rejects the
  beat; `apply_pacing` clamps and a test covers it.

## 12. Open decisions (resolve at spec review)

1. **Display-code mapping rule** (§3.2): nearest-preceding-kept-line with
   following fallback. Accept the heuristic, or require a hand-authored
   `display_code` per solution (higher fidelity, 103-entry maintenance)?
2. **Annotation primitive** (§5): reuse `rect`+`text` (no validator change) or
   add an `annotation` shape type (cleaner contract, validator change)?
