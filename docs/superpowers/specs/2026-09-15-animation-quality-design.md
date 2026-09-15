# Animation Quality Upgrade — Design Spec (Approach A)

Date: 2026-09-15
Issue: #162
Branch: `feat/162-animation-quality` in `../CodeCoach-AI-anim-quality`
Status: Proposed — awaiting user review before implementation plans

## 1. Problem

Backend already generates cinematic generic scenes (`shapes/motion/camera/badge/narration`
via `scene_planner.py` + `family_compilers.py`, gated by `AnimationValidator` +
`lint_quality`). But:

- `frontend/src/components/visualization/AnimationScriptRenderer.tsx` only knows
  `linear_search` / `code_comparison`. All 8 families fall back to `FallbackTrace`
  (plain text list). Cinematic beats never reach the viewer.
- `AnimationPlayer.tsx` is a basic stepper (play/pause/speed). No easing, no camera
  zoom/pan, no badge, no narration panel, limited a11y.
- Planner narrations are terse (`"Compare [1,2]"`, `"Swap [a] ↔ [b]"`), some beats miss
  camera, final beat sometimes misses badge, duplicate narrations exist
  (all currently only `lint_quality` warnings, not enforced).
- Non-array families use placeholder rects (`_root_shape` / `_item_shape` grid) instead
  of real layouts; tree/graph/stack/intervals lack parity with array.
- `downsample_steps(limit=96)` preserves key actions but can drop story beats
  (first/compare/swap/found ordering) on long traces.

Goal: React-first cinematic upgrade (no new runtime deps), covering all four pillars:
rich viewer rendering, smoother motion/visuals, clearer pedagogy, family parity.
Contract-stable, production-safe, TDD, `ANIMATION` gate stays green (`steps >= 3`).

## 2. Architecture

Keep pipeline unchanged:

```
question → resolve_algorithm → parse_input_kwargs → wrap_traced_solution
  → executor (Piston) → parse_trace → scene_planner.plan(spec) [primary]
  → family_compilers.compile_family [fallback]
  → AnimationValidator.validate → lint_quality (observable)
  → API AnimationScript {title, data, steps[{narration, shapes, motion, camera?, badge?}]}
  → AnimationScriptRenderer → GenericSceneRenderer + AnimationPlayer
```

- No schema change. `AnimationScript` / `AnimationStep` / `MotionOp` / `SceneShape`
  in `frontend/src/types/index.ts` stay backward-compatible. `type` stays legacy-optional.
- Motion ops stay Motion Canvas-compatible
  (`appear/disappear/move/fill/stroke/scale/rotate/label`, durations 0.1–5.0s) so a
  future Motion Canvas swap is a renderer change, not a contract change.
- Validator caps stay: `MAX_STEPS 100`, `MAX_SHAPES 120`, `MAX_SHAPES_PER_STEP 40`,
  `MAX_MOTIONS_PER_STEP 30`, `MIN_STEPS 3`, `MIN_SHAPES_TOTAL 2`.
- Failure semantics unchanged: any unusable input/trace/compile returns `None`,
  endpoint degrades gracefully (no 500 on bad trace).

## 3. Components (4 parallel workstreams)

### A1 — Viewer: GenericSceneRenderer + AnimationPlayer upgrade
Files: `frontend/src/components/visualization/AnimationScriptRenderer.tsx`,
new `GenericSceneRenderer.tsx`, `AnimationPlayer.tsx`, `types/index.ts` (minor),
tests `AnimationScriptRenderer.test.tsx`, new `GenericSceneRenderer.test.tsx`,
`AnimationPlayer.test.tsx`, Playwright scrub spec.

- `AnimationScriptRenderer`: route generic scenes (no legacy `type`, or unknown `type`)
  to `GenericSceneRenderer` instead of `FallbackTrace`. Keep legacy visualizers +
  `FallbackTrace` only for empty/invalid scripts.
- `GenericSceneRenderer` (new, SVG, 1920×1080 center-origin to match validator bounds
  `BOUND_X 960 / BOUND_Y 540`): render `rect/ellipse/line/polygon/text` with
  a frontend token mirror (`frontend/src/components/visualization/animationTokens.ts`,
  values copied from backend `animation_design_tokens.py`, backend remains source of truth);
  apply `motion` per beat with CSS transitions
  (durations from op, easing ease-out); implement `camera` (`reset/focus/panTo` with
  `zoom_focus 1.25 / zoom_full 1.0` via SVG viewBox transform); render `badge`
  (time/space) on final beat; narration panel (current + prev/next peek).
- `AnimationPlayer`: keep stepper API (`steps`, `children(step,index)`), add timeline
  scrub (range input), easing-aware auto-advance (use max motion duration per beat,
  clamped to speed preset), keyboard (space/arrows), `aria-live` narration,
  `prefers-reduced-motion` support (instant transitions), auto-pause on `found` kept.
- Defensive: empty steps → `null`; motion targeting unknown shape id or out-of-range
  coordinates → skip that op, `console.warn`, keep narration (never clamp — clamping
  would hide backend bound violations the validator must catch).

### A2 — Pedagogy: narration + camera + badge enrichment
Files: `backend/app/services/scene_planner.py`, tests `test_scene_planner*` /
`test_solution_animation_service.py`, `test_animation_coverage.py`.

- Narrations include values + why: `f"Compare arr[{i}]={a} vs arr[{j}]={b} — …"`,
  `f"Swap [{a}]={va} ↔ [{b}]={vb}"`, `f"Write [{idx}] = {val}"`,
  `f"Window [{low}..{high}] (len …)"`, `f"Found {target} at [{idx}]"`.
  Truncate to 300 chars (validator `MAX_NARRATION`). No duplicate consecutive narrations
  (append disambiguator or merge beats).
- Every focus beat carries `camera` (`focus` with `region`/`element` + zoom). Intro beat
  carries `camera.reset`. Final beat carries `badge {time, space}` + complexity narration.
- Keep `plan()` dispatcher signature; per-family helpers keep `(spec) -> beats` shape.
- Acceptance: `lint_quality` returns zero warnings on all 103 canonical
  `examples[0].input` traces (measured via `scripts/animate_coverage.py`); `beats >= 3`.

### A3 — Family parity: real layouts from design tokens
Files: `scene_planner.py` (`plan_tree`, `plan_graph`, `plan_stack`, `plan_intervals`,
`plan_linked_list`, `plan_backtrack`), `animation_design_tokens.py` (extend only,
no rename), `family_compilers.py` (fallback path parity where cheap).

- Tree: level-order layout ported once from `_compile_tree._tree_layout` into a shared
  helper (`scene_planner._tree_layout`, family_compilers imports it — no duplication),
  edges as `line` shapes, visit/choose/backtrack with highlight/dim.
- Graph/grid: circular layout radius 230 (parity with `_compile_graph`), edges stroked
  on traverse, visited nodes filled; grid cells from `cell_x/cell_y` with `GRID_CELL/GAP`.
- Stack: vertical box + items (`STACK_BOX_W/H`, item height), push = appear+move in,
  pop = move out + disappear; queue reuses stack with shifted layout (existing behavior kept).
- Intervals: horizontal bars scaled to `[lo,hi]` span, visit/mark semantics.
- Linked list: nodes + arrows + null terminator + pointer triangles (parity with compiler).
- All shapes/positions reuse `tokens.PALETTE/DURATION/CAMERA/ROW_Y`; no hard-coded colors
  outside tokens (new token keys allowed, old keys frozen).
- Acceptance: per-family golden test (one canonical question each) asserts layout bounds
  (all `x` in ±960, `y` in ±540), `steps >= 3`, camera present, badge present.

### A4 — Quality gates: lint + downsampling + coverage
Files: `animation_validator.py` (`lint_quality`), `solution_animation_service.py`
(`downsample_steps`), `scripts/animate_coverage.py`, QA budgets.

- `lint_quality` stays non-blocking at runtime (contract stability) but CI asserts
  zero warnings over the canonical corpus (new `test_animation_quality_gates.py` that
  runs `build_animation` with fake executor over all catalog `examples[0]`, budget
  < 60s via fake executor + `downsample_steps` already capped at 96).
  Checks: camera present ≥1 beat, badge on final beat, no empty narration,
  no duplicate consecutive narration.
- `downsample_steps(limit=96)`: preserve story skeleton — always keep first intro beat,
  last outro beat, all `found/not_found/mark/swap/write/partition/edge/choose/backtrack`,
  then stride-sample the rest (`compare/pointer/read/visit`) in original order.
  Keep current `_DOWNSAMPLE_KEEP` set; add ordering guarantee + test.
- Coverage: `qa/enforce_coverage_budget.py` must not regress; new tests cover new branches.

## 4. Data flow

Unchanged from §2. Renderer is pure: `(script, stepIndex) -> SVG`. Player owns
`currentIndex/isPlaying/speedMs`. No new network calls, no new stores, no DB changes
(Supabase untouched). No Piston/Groq path changes; animation still visualizes the
**optimal solution only**, never student code.

## 5. Error handling / failure modes

- Backend: `build_animation` returns `None` on unknown algo, missing examples, empty
  kwargs, executor `HTTPException`, non-zero exit, malformed/empty trace, planner beats
  `< 3`, validator failure. All paths log with algorithm tag (`logger.warning`) — keep.
- Frontend: invalid script → `FallbackTrace` (existing) only when `steps` empty or
  shapes/motion malformed; per-beat motion errors isolated (skip op, keep narration).
- Validator: hard failures (bounds, caps, unknown target, no-transform step) unchanged.
  No new hard rules (to keep `ANIMATION` gate green during rollout); quality enforced
  via A4 CI corpus test, not runtime rejection.
- Accessibility: `prefers-reduced-motion` disables transitions; keyboard fully operable;
  narration in `aria-live="polite"`.

## 6. Testing (TDD — red → green → refactor)

- Backend unit: planner narration/camera/badge per family; downsampling story preservation;
  lint gates over fixtures. Run: `python -m pytest tests/unit`.
- Backend integration: `build_animation` over canonical corpus with fake executor;
  `ANIMATION` use-case (`test_admin_validate_question`, `test_animation_coverage`)
  stays green. Run: `python -m pytest tests/integration` with isolated Supabase schema.
- Contract/security/perf/migrations suites unchanged, must stay green.
- Frontend: `pnpm typecheck`, `pnpm lint`, `pnpm test:run` (new renderer/player tests),
  `pnpm test:e2e` (Playwright scrub + keyboard + badge assertions).
- Lint/format: `ruff check .`, `ruff format . --check`.
- No coverage budget regression (`qa/enforce_coverage_budget.py`); flaky tests go to
  quarantine manifest, not committed suite.

## 7. Rollout / ops

- No migrations, no env changes, no new deps. Cloudflare Workers-safe (SVG+CSS only).
- Small PRs per workstream (A1…A4), each behind existing contract (no flag needed;
  renderer change is additive — old fallback remains for invalid scripts).
- Observability: keep `logger.warning("Animation quality (%s): %s")`; add counter log
  in `animate_coverage.py` (warn count per family) for CI visibility.
- After merge: `graphify update .`, PR with `Closes #162`.

## 8. Non-goals (explicit)

- No Motion Canvas adoption, no video/MP4 export in this spec (deferred; contract kept ready).
- No new families or algorithms; no question-bank additions.
- No API schema breaking changes; no DB changes; no auth/billing changes.
- No 3D, no sound, no autoplay with sound.

## 9. Subagent split (after spec approval → writing-plans)

- Agent A1: frontend viewer (GenericSceneRenderer + Player). Scope: `frontend/src/...`.
  Must not touch backend. Output: green `typecheck + test:run + test:e2e` subset.
- Agent A2: pedagogy (planner narrations/camera/badge). Scope: `scene_planner.py` only.
  Must not change validator caps. Output: zero `lint_quality` warnings on fixtures.
- Agent A3: family layouts. Scope: `scene_planner.py` family helpers + tokens (additive).
  Must keep dispatcher signature. Output: per-family golden tests green.
- Agent A4: gates (lint CI test + downsampling). Scope: `animation_validator.py`
  (lint only), `solution_animation_service.py` (`downsample_steps` only), new tests.
  Must not make lint blocking at runtime.

Integration: land A2+A3 first (backend beats), then A1 (renderer consumes them), A4
guards all. Full suite green before merge.

## 10. Self-review

- Placeholders: none — all file paths, caps, token keys concrete.
- Consistency: validator caps referenced identically in §2/§5; camera/badge requirements
  match `lint_quality` semantics; downsampling limit 96 matches service default.
- Scope: single spec, 4 parallelizable workstreams, each reviewable; non-goals prevent creep.
- Ambiguity resolved: React/SVG (not Motion Canvas); lint non-blocking at runtime but
  blocking in CI corpus test; fallback text retained only for invalid scripts.
