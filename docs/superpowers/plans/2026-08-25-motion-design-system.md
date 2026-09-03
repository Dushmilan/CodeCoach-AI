# Motion Design System — Algorithm-to-Animation Engine

Date: 2026-08-25
Branch: `feat/motion-design-system` (from `main` @ `7fefe09` — PR #119 merged)
Status: Draft — ready for TDD slice 1

## Objective
Replace the generic "boxes moving" debugger animation (`animation_compiler.py` / `family_compilers.py` → `viewer.tsx:renderGenericScene`) with a **motion-design layer** that turns `AlgorithmSpecification → Scene Plan → Visual Design System → Motion Canvas` into polished 9:16/16:9 social videos — cinematic, not literal.

## Context (what exists)
- Pipeline today: `SolutionAnimationService.build_animation(question) → Piston(trace) → parse_trace → compile_family → AnimationValidator → /api/coach/animate → postMessage(token) → motion-canvas-lab/src/scenes/viewer.tsx:260` (`AnimationScript{steps{narration,shapes,motion}}`, caps `MAX_CELLS 48 / MAX_SHAPES 120 / MIN_STEPS 3`).
- `AnimationScript` is optimal-solution only (student code never used `coach.py:195`). Groq fallback authors geometry — to be removed (LLM → narration only).
- Two renderers diverge: Motion Canvas iframe `:9000` (cinematic) vs `AnimationPlayer.tsx` React (interactive). CSP `frame-src viewer`.
- Quality gap: literal `compare→fill, swap→move` per step, static camera, no typography hierarchy.

## Architecture (from user spec)

```
AlgorithmSpecification{algorithm, visualization, initialState, steps: AnimationStep[], complexity{time,space}}
        ↓
Scene Planner  — semantic → motion beats (highlight midpoint, discard left, focus region, show complexity)
        ↓
Visual Design System  — primitives
        ↓
Motion Primitives → Renderer (Motion Canvas) → 9:16 / 16:9 MP4 via FFmpeg
```

Student code stays separate: `Student Code → Code Evaluation → Feedback` (no feed into animation).

## Design System — primitives

**Components (CodeCoach Motion Library):**
`Array({element,index,value,highlight})`, `Pointer(low/mid/high)`, `Arrow`, `Graph(node,edge,queue,stack)`, `Stack/CallStack`, `Tree`, `CodeBlock`, `Label`, `ComplexityBadge`

**Motion:**
`enter/exit/highlight/pulse/moveTo/transform/morph/focus/shake/stagger`, plus `spring/fade/scale`

**Typography:**
One display + one mono `JetBrains Mono` (already `viewer.tsx:194`), large numbers `O(log n) / 42 > 27 / SEARCH RIGHT`, limited text, hierarchy via size/weight/color not paragraphs. Narration holds explanation.

**Camera:**
`camera.focus(element) / zoom(1.25) / panTo(region) / reset()` — reusable. `Binary search: full array → focus mid → dim left half → pan to remaining → new mid`.

## Templates (build 3 first, then extend)

1. **Sorting** (bubble/merge/quick): `bars, comparisons, swaps, partition regions, pointers` — stagger, partition dim.
2. **Searching** (binary): `array, low/high/mid, search region, discarded region, camera` — the hero 9:16 mock (`BINARY SEARCH / Find 42 / 12 18 27 35 42 ... ↑ MID / O(log n)`).
3. **Graphs** (BFS/DFS/Dijkstra): `nodes, edges, visited, queue/stack, distance labels, path highlight`.

DB stores semantic instructions, not coordinates: `"highlight midpoint" → planner → motion`.

## Scope — Slice 1 (this PR)

**Do:**
- Introduce `AlgorithmAnimation` schema (TS + Pydantic `AlgorithmSpec`) with `visualization in {sorted-array, bars, graph, tree}` and the binary-search example (`array [2,4,7,9,13...] target 13 → set_bounds/inspect_mid/discard_left...`).
- Add `ScenePlanner` (pure, unit-tested) that maps `AlgorithmAnimation.steps` → `SceneBeat[]` (searching template) with camera directives.
- Extend `viewer.tsx` with `CodeCoach Motion Library` components + `camera` system behind feature flag; keep `renderGenericScene` as fallback (contract stable, existing `AnimationScript` still validated).
- One polished **Searching** template end-to-end (binary search 9:16 composition with typography tokens).

**Don't:**
- Student-code trace instrumentation (Idea #7), video export/FFmpeg, DB migration for `animations` cache, Remotion adapter (Phase 2).

## TDD Plan

1. **Red:** `backend/tests/unit/test_scene_planner.py` — `set_bounds low=0 high=6 → focus region [0,6]`, `inspect_mid 3 → highlight mid + camera.focus(cell_3)`, `discard_left until 4 → dim [0,3] + panTo([4,6])`, `complexity O(log n) → ComplexityBadge`.
2. **Green:** `backend/app/services/scene_planner.py` + `animation_design_tokens.py` (typography/spacing/camera).
3. **Red:** `motion-canvas-lab/src/scenes/viewer-motion-design.test.ts` — snapshot steps contain `highlight/mid` beats.
4. **Green:** `viewer.tsx` `renderSearchingScene` + `Array/Pointer/ComplexityBadge` components.

## Verification

- `python -m pytest backend/tests/unit/test_scene_planner.py -v` + `ruff check .`
- `pnpm --filter motion-canvas-lab typecheck && pnpm test:run` (viewer scene)
- manual `POST /api/coach/animate` with binary-search fixture → viewer renders beats, no 502.
- Docker: `docker-compose up -d --build` (lab dist copied into `frontend` image or `viewer.html` served statically).

## Risks

- Motion Canvas bundle size / `:9000` dev friction → mitigate by copying `dist/viewer.html` into `frontend/public` in Docker (single image).
- Validator caps (`MAX_SHAPES 120`) — design beats must stay under cap; stagger beats split steps.
- Typography overuse → enforce token `MAX_NARRATION 300` already `validator.py:64`.

## Next phases (out of scope)

- Phase 2: Remotion export (`AlgorithmSpec → Remotion <AlgorithmVideo trace={}>`), `templates/sorting/graphs`.
- Phase 3: Student trace diff replay (Instrument arbitrary submissions, Idea #7).
