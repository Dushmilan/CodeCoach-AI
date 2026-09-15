# A1 Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render generic AnimationScript scenes cinematically in React/SVG instead of fallback text.

**Architecture:** Add `GenericSceneRenderer.tsx` (pure SVG renderer for shapes/motion/camera/badge/narration) plus `animationTokens.ts` mirror; route unknown/missing `type` to it; upgrade `AnimationPlayer` with scrub/keyboard/reduced-motion. No new deps.

**Tech Stack:** Next.js 14, React, TypeScript, SVG + CSS transitions, Vitest + Testing Library, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-15-animation-quality-design.md` (§3 A1, §4, §5)

## Global Constraints

- No API schema change; `AnimationScript/AnimationStep/MotionOp/SceneShape` stay backward-compatible.
- Validator bounds respected: x in ±960, y in ±540; durations 0.1–5.0s.
- Invalid ops skipped with `console.warn`, never crash, never clamp coordinates.
- TDD red → green → refactor; `pnpm typecheck`, `pnpm lint`, `pnpm test:run` green.
- Accessibility: keyboard operable, `aria-live="polite"` narration, `prefers-reduced-motion` disables transitions.
- Backend untouched by this plan.

---

### Task 1: Frontend token mirror

**Files:**
- Create: `frontend/src/components/visualization/animationTokens.ts`
- Test: `frontend/src/components/visualization/animationTokens.test.ts`

**Interfaces:**
- Consumes: backend `backend/app/services/animation_design_tokens.py` values (copied verbatim).
- Produces: `TOKENS = { palette, duration, camera, rowY, cellLabelSize, maxLabel }` used by Task 2.

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect } from "vitest";
import { TOKENS } from "./animationTokens";

describe("animationTokens", () => {
  it("mirrors backend palette and camera", () => {
    expect(TOKENS.palette.highlight_fill).toBe("#1d4ed8");
    expect(TOKENS.camera.zoom_focus).toBe(1.25);
    expect(TOKENS.camera.zoom_full).toBe(1.0);
    expect(TOKENS.duration.highlight).toBe(0.35);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/components/visualization/animationTokens.test.ts`
Expected: FAIL with "No such file" / "Cannot find module './animationTokens'"

- [ ] **Step 3: Write minimal implementation**

```ts
export const TOKENS = {
  palette: {
    idle_fill: "#1e293b",
    idle_stroke: "#334155",
    highlight_fill: "#1d4ed8",
    highlight_stroke: "#3b82f6",
    dim_fill: "#0f172a",
    dim_stroke: "#1e293b",
    accent: "#facc15",
    success_fill: "#14532d",
    success_stroke: "#22c55e",
    muted: "#94a3b8",
    text: "#e2e8f0",
  },
  duration: { enter: 0.4, highlight: 0.35, focus: 0.5, dim: 0.3, stagger: 0.08 },
  camera: { zoom_focus: 1.25, zoom_full: 1.0, pan_duration: 0.5 },
  rowY: 0,
  cellLabelSize: 28,
  maxLabel: 24,
} as const;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/components/visualization/animationTokens.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/visualization/animationTokens.ts frontend/src/components/visualization/animationTokens.test.ts
git commit -m "feat(162): add frontend animation token mirror"
```

### Task 2: GenericSceneRenderer

**Files:**
- Create: `frontend/src/components/visualization/GenericSceneRenderer.tsx`
- Test: `frontend/src/components/visualization/GenericSceneRenderer.test.tsx`
- Modify: `frontend/src/components/visualization/index.ts` (export)

**Interfaces:**
- Consumes: `TOKENS` from Task 1; `AnimationScript, AnimationStep` from `@/types`.
- Produces: `<GenericSceneRenderer script step stepIndex />` rendering SVG + narration + badge.

- [ ] **Step 1: Write the failing test**

```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GenericSceneRenderer } from "./GenericSceneRenderer";

const script = {
  title: "Bubble Sort",
  data: { family: "array" },
  steps: [
    {
      narration: "Compare arr[0]=5 vs arr[1]=1",
      shapes: [
        { id: "cell_0", type: "rect", x: -50, y: 0, width: 88, height: 88, fill: "#1e293b", stroke: "#334155" },
        { id: "val_0", type: "text", x: -50, y: 0, text: "5", fontSize: 28, fill: "#e2e8f0" },
      ],
      motion: [{ target: "cell_0", op: "fill", to: "#1d4ed8", duration: 0.35 }],
      camera: { action: "focus", region: [0, 1] },
    },
    {
      narration: "Complexity O(n²) time, O(1) space",
      shapes: [],
      motion: [{ target: "cell_0", op: "scale", to: 1.0, duration: 0.25 }],
      badge: { time: "O(n²)", space: "O(1)" },
    },
  ],
};

describe("GenericSceneRenderer", () => {
  it("renders shapes, narration, and badge", () => {
    render(<GenericSceneRenderer script={script as never} step={script.steps[1] as never} stepIndex={1} />);
    expect(screen.getByText("Complexity O(n²) time, O(1) space")).toBeInTheDocument();
    expect(screen.getByText("O(n²)")).toBeInTheDocument();
  });
  it("skips unknown motion targets without crashing", () => {
    const bad = { ...script.steps[0], motion: [{ target: "nope", op: "fill", to: "#1d4ed8", duration: 0.3 }] };
    const { container } = render(<GenericSceneRenderer script={script as never} step={bad as never} stepIndex={0} />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/components/visualization/GenericSceneRenderer.test.tsx`
Expected: FAIL with "Cannot find module './GenericSceneRenderer'"

- [ ] **Step 3: Write minimal implementation**

```tsx
"use client";
import { AnimationScript, AnimationStep } from "@/types";
import { VisualizerProps } from "./AnimationScriptRenderer";

export function GenericSceneRenderer({ script, step }: VisualizerProps) {
  void script;
  const shapes = Array.isArray(step?.shapes) ? step.shapes : [];
  const badge = (step as unknown as { badge?: { time: string; space: string } }).badge;
  const known = new Set(shapes.map((s) => (s as { id: string }).id));
  const motions = (Array.isArray(step?.motion) ? step.motion : []).filter((m) =>
    known.has((m as { target: string }).target),
  );
  void motions;
  return (
    <div>
      <svg viewBox="-960 -540 1920 1080" role="img" aria-label={step?.narration ?? "animation"}>
        {shapes.map((s) => {
          const sh = s as { id: string; type: string; x?: number; y?: number; text?: string; width?: number; height?: number; fill?: string };
          if (sh.type === "text") return <text key={sh.id} x={sh.x ?? 0} y={sh.y ?? 0} fill={sh.fill ?? "#e2e8f0"}>{sh.text ?? ""}</text>;
          if (sh.type === "rect" || sh.type === "ellipse")
            return <rect key={sh.id} x={(sh.x ?? 0) - (sh.width ?? 0) / 2} y={(sh.y ?? 0) - (sh.height ?? 0) / 2} width={sh.width ?? 0} height={sh.height ?? 0} fill={sh.fill} />;
          return null;
        })}
      </svg>
      <p aria-live="polite">{step?.narration}</p>
      {badge ? <div><span>{badge.time}</span><span>{badge.space}</span></div> : null}
    </div>
  );
}
```

Expand in refactor steps to cover `line/polygon`, camera viewBox transform, CSS transitions. Keep pure.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/components/visualization/GenericSceneRenderer.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/visualization/GenericSceneRenderer.tsx frontend/src/components/visualization/GenericSceneRenderer.test.tsx frontend/src/components/visualization/index.ts
git commit -m "feat(162): add generic scene renderer"
```

### Task 3: Router — generic scenes to new renderer

**Files:**
- Modify: `frontend/src/components/visualization/AnimationScriptRenderer.tsx`
- Test: `frontend/src/components/visualization/AnimationScriptRenderer.test.tsx`

**Interfaces:**
- Consumes: `GenericSceneRenderer` from Task 2.
- Produces: unknown/missing `type` with valid generic steps renders SVG, not fallback text.

- [ ] **Step 1: Write the failing test**

```tsx
it("renders generic scenes with the cinematic renderer", () => {
  const generic = {
    title: "Bubble Sort",
    data: { family: "array" },
    steps: [
      { narration: "Intro", shapes: [{ id: "cell_0", type: "rect", x: 0, y: 0, width: 88, height: 88 }], motion: [{ target: "cell_0", op: "appear", duration: 0.4 }] },
      { narration: "Compare", shapes: [], motion: [{ target: "cell_0", op: "fill", to: "#1d4ed8", duration: 0.3 }] },
      { narration: "Done", shapes: [], motion: [{ target: "cell_0", op: "scale", to: 1.0, duration: 0.25 }] },
    ],
  };
  const { container } = render(<AnimationScriptRenderer script={generic as never} />);
  expect(container.querySelector("svg")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/components/visualization/AnimationScriptRenderer.test.tsx`
Expected: FAIL with "Unable to find svg" (currently falls back to text trace)

- [ ] **Step 3: Write minimal implementation**

Route: if `script.type` missing or not in `VISUALIZERS`, and steps look generic (have `shapes`/`motion`), render `AnimationPlayer` + `GenericSceneRenderer`; keep `FallbackTrace` only when steps empty or no shapes/motion anywhere.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/components/visualization/AnimationScriptRenderer.test.tsx`
Expected: PASS (update the old "renders a plain trace for unsupported animation types" test to use a script with no shapes/motion so it still covers the invalid-script fallback)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/visualization/AnimationScriptRenderer.tsx frontend/src/components/visualization/AnimationScriptRenderer.test.tsx
git commit -m "feat(162): route generic scenes to cinematic renderer"
```

### Task 4: AnimationPlayer upgrade

**Files:**
- Modify: `frontend/src/components/visualization/AnimationPlayer.tsx`
- Test: `frontend/src/components/visualization/AnimationPlayer.test.tsx` (new; existing player tests live in `AnimationScriptRenderer.test.tsx` and must stay green)

**Interfaces:**
- Consumes: `steps` (unchanged props).
- Produces: same props plus scrub slider, keyboard, reduced-motion, aria-live.

- [ ] **Step 1: Write the failing test**

```tsx
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AnimationPlayer } from "./AnimationPlayer";

const steps = [{ narration: "One" }, { narration: "Two" }, { narration: "Three" }];

describe("AnimationPlayer scrub", () => {
  it("scrubs via slider and announces narration", () => {
    render(<AnimationPlayer steps={steps as never}>{(s) => <div>{(s as { narration: string }).narration}</div>}</AnimationPlayer>);
    fireEvent.change(screen.getByRole("slider", { name: /animation progress/i }), { target: { value: "2" } });
    expect(screen.getByText("Three")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm vitest run src/components/visualization/AnimationPlayer.test.tsx`
Expected: FAIL with "Unable to find slider"

- [ ] **Step 3: Write minimal implementation**

Add `<input type="range" aria-label="Animation progress" min={0} max={stepCount-1} value={currentIndex} />` wired to `stepTo`; add `onKeyDown` for arrows/space on the player root; wrap narration region with `aria-live="polite"` in callers (renderer already does); respect `matchMedia("(prefers-reduced-motion: reduce)")` by skipping interval auto-advance animation delay (set speedMs floor behavior unchanged, transitions via CSS media query).

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm vitest run src/components/visualization/AnimationPlayer.test.tsx src/components/visualization/AnimationScriptRenderer.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/visualization/AnimationPlayer.tsx frontend/src/components/visualization/AnimationPlayer.test.tsx
git commit -m "feat(162): add player scrub and a11y"
```

### Task 5: Verify

- [ ] Run `pnpm typecheck`, `pnpm lint`, `pnpm test:run` — all green.
- [ ] Run Playwright scrub spec: `pnpm test:e2e` (or targeted spec) covering scrub slider, keyboard, badge visible on final beat.
