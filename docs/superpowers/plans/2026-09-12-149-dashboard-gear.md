# Dashboard Gear Menu + SVG Skill Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close issue #149 — Dashboard reachable from the gear menu tabs and the skill graph rendered as SVG, with the `/dashboard` route intact.

**Architecture:** Promote the existing `SettingsModal.tsx` `settings|dashboard|skills` tabs from link-card placeholders to embedded views reusing `SkillGraph.tsx` (SVG + `computeLayout`) and `use-skill-graph.hook.ts`. Keep `/dashboard/page.tsx` routable; `Header.tsx` gear wiring unchanged.

**Tech Stack:** Next.js 14 App Router, TypeScript, Tailwind, `SkillGraph` SVG, Vitest + Testing Library + MSW.

**Spec:** GitHub issue #149 body — move Dashboard into gear-icon tabs; render skill graph as SVG in Dashboard (`SkillGraph.tsx` + `use-skill-graph.hook.ts`); Header/SettingsModal wiring + skill-graph service/type updates. Note: `feat/dashboard-skills-gear` (`45b0e68`) already merged via PR #150, so this plan covers the remaining gaps: the gear `dashboard` tab is still a link card (`SettingsModal.tsx:33-41`) and the `skills` tab still shows the list-style `SkillGraphInline.tsx` instead of the SVG graph.

## Global Constraints

- Preserve the `/dashboard` route and API contracts (`GET /api/skills/me/skills?include_boilerplate`, `/boilerplate`, `/sync` in `skill-graph.service.ts:8-35`).
- Dashboard stays out of the top-level nav (`Header.tsx:44-45` comment "Dashboard moved to gear menu").
- TDD red → green → refactor; `pnpm lint`, `pnpm typecheck`, `pnpm test:run` green before PR.
- One Issue = one branch = one worktree (`feat/149-dashboard-skills-gear` in `../CodeCoach-AI-149-dashboard-gear`).

---

### Task 1: Embed Dashboard content in gear `dashboard` tab (not just link)

**Files:**
- Modify: `frontend/src/components/settings/SettingsModal.tsx:33-41`
- Reuse: `frontend/src/app/dashboard/page.tsx:70-78` blocks (`SkillGraph`, `LearningSignals`, `MemoryGraph`, queues) or extract a shared component
- Test: `frontend/src/components/settings/SettingsModal.test.tsx` (create or extend)

**Interfaces:**
- Consumes: existing tab state (`Tab`, `data-testid=settings-tab-dashboard`, `settings-dashboard-tab`)
- Produces: embedded dashboard summary in modal; "Open Dashboard" button retained as escape hatch (`data-testid=settings-dashboard-open`)

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/components/settings/SettingsModal.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SettingsModal } from './SettingsModal';

test('gear dashboard tab embeds the skill graph, not just a link', async () => {
  render(<SettingsModal open onClose={() => {}} isAuthenticated />);
  fireEvent.click(screen.getByTestId('settings-tab-dashboard'));
  expect(await screen.findByTestId('settings-dashboard-tab')).toBeInTheDocument();
  expect(screen.getByTestId('settings-dashboard-open')).toBeInTheDocument();
  // NEW: embedded content, not just a link card
  expect(await screen.findByTestId('skill-graph')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter frontend test:run SettingsModal` (adjust to repo script; root `frontend/` uses `pnpm test:run`)
Expected: FAIL — no `skill-graph` inside the modal (only the link card).

- [ ] **Step 3: Write minimal implementation**

```tsx
// SettingsModal.tsx — dashboard tab
{tab === 'dashboard' && (
  <div className="space-y-3" data-testid="settings-dashboard-tab">
    <div className="max-h-96 overflow-y-auto pr-1">
      <SkillGraph />
    </div>
    <button
      onClick={() => { window.location.href = '/dashboard'; onClose(); }}
      data-testid="settings-dashboard-open"
      className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-white text-black px-4 py-1.5 text-xs font-medium hover:bg-white/90 transition-colors"
    >
      <LayoutDashboard className="h-3.5 w-3.5" /> Open Dashboard
    </button>
  </div>
)}
```

Import `SkillGraph` from `@/features/skill-graph/SkillGraph`. Keep the modal scrollable (`max-h-[85vh]` container already scrolls).

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter frontend test:run SettingsModal`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/settings/SettingsModal.tsx frontend/src/components/settings/SettingsModal.test.tsx
git commit -m "feat(149): embed dashboard graph in gear tab"
```

### Task 2: Skills tab renders SVG graph (replace / augment list)

**Files:**
- Modify: `frontend/src/components/settings/SettingsModal.tsx:42-49`, possibly `frontend/src/features/skill-graph/SkillGraphInline.tsx` (add `variant` prop) or swap to `SkillGraph`
- Reuse: `frontend/src/features/skill-graph/SkillGraph.tsx:142-171` SVG (`data-testid=skill-graph-node/edge`), `computeLayout:22-63`
- Test: `frontend/src/components/settings/SettingsModal.test.tsx` + existing `SkillGraph` tests

**Interfaces:**
- Consumes: `useSkillGraph(true)` hook return (`graph`, `isLoading`, `error`, `refresh`, `syncFromSubmissions`)
- Produces: skills tab showing `data-testid="skill-graph"` with `skill-graph-node` count > 0

- [ ] **Step 1: Write the failing test**

```tsx
test('gear skills tab renders the SVG graph', async () => {
  render(<SettingsModal open onClose={() => {}} isAuthenticated />);
  fireEvent.click(screen.getByTestId('settings-tab-skills'));
  const graph = await screen.findByTestId('skill-graph');
  expect(graph).toBeInTheDocument();
  expect(graph.querySelectorAll('[data-testid="skill-graph-node"]').length).toBeGreaterThan(0);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter frontend test:run SettingsModal`
Expected: FAIL — skills tab shows `skill-graph-list` items, not the SVG `skill-graph`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// SettingsModal.tsx — skills tab
{tab === 'skills' && (
  <div className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4" data-testid="settings-skills-tab">
    <div className="max-h-96 overflow-auto">
      <SkillGraph />
    </div>
  </div>
)}
```

Handle modal height/scroll via the wrapper (`max-h-96 overflow-auto`; SVG already has `overflow-x-auto`). If the full `SkillGraph` header is too heavy for the modal, add a `compact` prop to `SkillGraph` hiding the legend/sync button — but only if the test run shows a layout problem.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm --filter frontend test:run SettingsModal`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/settings/SettingsModal.tsx frontend/src/components/settings/SettingsModal.test.tsx
git commit -m "feat(149): render SVG skill graph in gear skills tab"
```

### Task 3: Service / type / header polish + close-out

**Files:**
- Check: `frontend/src/features/skill-graph/skill-graph.service.ts`, `frontend/src/types/index.ts` (`SkillGraphResponse`, `SkillSummary`), `frontend/src/components/header/Header.tsx`
- Test: `frontend/src/features/skill-graph/skill-graph.service.test.ts`, `frontend/src/app/dashboard/page.test.tsx`

**Interfaces:**
- Consumes: `GET /api/skills/me/skills?include_boilerplate`, `GET /api/skills/boilerplate`, `POST /api/skills/me/sync`
- Produces: no contract changes; unauthenticated → `getBoilerplate()`, authenticated → `getGraph(true)`

- [ ] **Step 1: Verify unauthenticated path** — gear tabs render boilerplate via `getBoilerplate()` without auth errors; authenticated path uses `getGraph(true)`. Add a test only if a gap is found.
- [ ] **Step 2: Verify mobile menu** (`Header.tsx:162-190`) does not re-add Dashboard as a top-level link; `/dashboard` stays directly routable.
- [ ] **Step 3: Run quality gates**

Run: `pnpm --filter frontend lint && pnpm --filter frontend typecheck && pnpm --filter frontend test:run`
Expected: all green.

- [ ] **Step 4: Open PR with `Closes #149`** in the description; `git push -u origin feat/149-dashboard-skills-gear`.
