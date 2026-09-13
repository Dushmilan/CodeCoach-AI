# Viewer Duration Lock Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tokened viewer plays the full real animation (18/18 beats) instead of looping early at the ~15s demo duration.

**Architecture:** Gate `Player` creation in `motion-canvas-lab/src/viewer-player.ts` on payload arrival (animation / error / timeout) when `?token` is present, so the Player's duration fast-forward measures the real branch. Untokened direct-open keeps the demo path unchanged.

**Tech Stack:** Motion Canvas (`Player`, `Stage`, `makeScene2D`), TypeScript, Playwright harness.

**Spec:** GitHub issue #155 — "Viewer timeline locked to demo duration — real animation truncated at ~15s, loops early". Root cause: Player computes scene duration by fast-forwarding the generator at load; payload posts ~1.5s after load, so the duration run takes the 5s-wait + 3-step cars demo branch (~15.5s / 932 frames @60fps) and locks; real 18-beat branch (~30s) overruns and `loop:true` reseeks to 0 forever.

## Global Constraints

- Preserve the `?token`-gated postMessage contract: `CODECOACH_ANIMATION` / `CODECOACH_ANIMATION_ERROR` + token match + `event.source === window.parent` (`motion-canvas-lab/src/scenes/viewer.tsx:157-173`).
- Keep untokened direct-open demo (`DEMO_ANIMATION`) working under `pnpm dev`.
- Never use a wall-clock `performance.now()` deadline inside the scene timeline (breaks fast-forward measurement — see `viewer.tsx:481-489` comment).
- TDD red → green → refactor; full related suite green before PR.
- One Issue = one branch = one worktree (`fix/155-viewer-duration` in `../CodeCoach-AI-155-viewer-duration`).

---

### Task 1: Reproduce with failing Playwright harness

**Files:**
- Create: `motion-canvas-lab/tests/viewer-duration.spec.ts`
- Modify: none
- Test: `motion-canvas-lab/tests/viewer-duration.spec.ts`

**Interfaces:**
- Consumes: `viewer.html?token=<nonce>` page, `#viewer-step-chip`, `#viewer-time` (built in `viewer-player.ts:79-82,120-122`)
- Produces: failing assertion — chip reaches `18 / 18`, time total exceeds demo lock (`> 0:20`)

- [ ] **Step 1: Write the failing test**

```ts
// motion-canvas-lab/tests/viewer-duration.spec.ts
import { test, expect } from '@playwright/test';

test('tokened 18-beat payload plays to 18/18 without early loop', async ({ page }) => {
  const token = 'test-155-' + Date.now();
  await page.goto(`/viewer.html?token=${token}`);
  // Mimic real launcher timing: payload posts ~1.5s after load,
  // after the Player has already fast-forwarded for duration.
  await page.waitForTimeout(1500);
  await page.evaluate(([t]) => {
    window.postMessage(
      {
        type: 'CODECOACH_ANIMATION',
        token: t,
        animation: {
          title: 'duration-probe',
          steps: Array.from({ length: 18 }, (_, i) => ({ narration: `step ${i + 1}` })),
        },
      },
      '*',
    );
  }, [token]);
  await expect(page.locator('#viewer-step-chip')).toContainText('18 / 18', { timeout: 45000 });
  const time = (await page.locator('#viewer-time').textContent()) ?? '';
  expect(time).toMatch(/0:(2\d|3\d|4\d|5\d)|1:/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm --filter motion-canvas-lab test viewer-duration` (adjust to the repo's actual script name; check `motion-canvas-lab/package.json`)
Expected: FAIL — chip loops `10/18 → 1/18`, time label shows `0:15 / 0:15`.

- [ ] **Step 3: Commit**

```bash
git add motion-canvas-lab/tests/viewer-duration.spec.ts
git commit -m "test(155): failing harness for tokened duration lock"
```

### Task 2: Defer Player creation until payload / error / timeout (tokened only)

**Files:**
- Modify: `motion-canvas-lab/src/viewer-player.ts:264-297` (`main()`)
- Modify: `motion-canvas-lab/src/scenes/viewer.tsx:29-30` (share/widen timeout constants only if needed)
- Test: `motion-canvas-lab/tests/viewer-duration.spec.ts`

**Interfaces:**
- Consumes: URL `token` (`new URLSearchParams(location.search).get('token')`), `CODECOACH_ANIMATION` / `CODECOACH_ANIMATION_ERROR` window messages
- Produces: `Player` constructed only after settle; `buildOverlay(player)` behavior unchanged

- [ ] **Step 1: Confirm red**

Run: `pnpm --filter motion-canvas-lab test viewer-duration`
Expected: FAIL (same as Task 1).

- [ ] **Step 2: Write minimal implementation**

```ts
// motion-canvas-lab/src/viewer-player.ts
const PAYLOAD_WAIT_MS = 8000;

function waitForPayload(token: string): Promise<void> {
  return new Promise((resolve) => {
    const timer = window.setTimeout(done, PAYLOAD_WAIT_MS);
    function done(): void {
      window.clearTimeout(timer);
      window.removeEventListener('message', onMessage);
      resolve();
    }
    function onMessage(event: MessageEvent): void {
      if (event.source !== window.parent) return;
      const data = event.data;
      if (!data || typeof data !== 'object') return;
      if (data.token !== token) return;
      if (data.type === 'CODECOACH_ANIMATION' || data.type === 'CODECOACH_ANIMATION_ERROR') {
        // Re-post so the scene bridge in scenes/viewer.tsx still receives it.
        window.postMessage(data, window.location.origin);
        done();
      }
    }
    window.addEventListener('message', onMessage);
  });
}

async function main(): Promise<void> {
  const token = new URLSearchParams(window.location.search).get('token');
  if (token) {
    // Wait for the launcher payload so the Player's duration
    // fast-forward measures the REAL branch, not the demo.
    await waitForPayload(token);
  }
  const stage = new Stage();
  // ... rest of main() unchanged (Player with loop:true, overlay, togglePlayback(true))
}
```

Notes:
- Token-absent path skips the wait entirely (demo as today).
- Timeout (~8s: covers launcher 1.5s + margin, still bounded) resolves so the viewer never hangs; error message resolves immediately.
- Alternative without re-post: expose payload on `window.__CODECOACH_PAYLOAD` consumed by the scene bridge. Pick one; re-post keeps a single contract.

- [ ] **Step 3: Run test to verify it passes**

Run: `pnpm --filter motion-canvas-lab test viewer-duration`
Expected: PASS — chip reaches `18 / 18`, time total `~0:30`.

- [ ] **Step 4: Regression checks**

- Direct open (no `?token`) still shows the demo cars scene and reaches `Complete`.
- `CODECOACH_ANIMATION_ERROR` post shows the error state, never hangs to timeout.

- [ ] **Step 5: Commit**

```bash
git add motion-canvas-lab/src/viewer-player.ts motion-canvas-lab/tests/viewer-duration.spec.ts
git commit -m "fix(155): gate Player creation on payload for tokened viewer"
```

### Task 3: Scrubber / duration hardening + cleanup

**Files:**
- Modify: `motion-canvas-lab/src/viewer-player.ts:60-70` (`timelineMaxFrames`), `:165-172` (`setProgress`)
- Test: `motion-canvas-lab/tests/viewer-duration.spec.ts` + existing viewer overlay tests

**Interfaces:**
- Consumes: `player.playback.duration`, `player.onDurationChanged`, `CODECOACH_VIEWER_STEP` messages
- Produces: scrubber max + time label bound to the real timeline; no demo-pass `Complete` flash on tokened loads

- [ ] **Step 1: Assert no demo-pass flash**

```ts
// extend viewer-duration.spec.ts
test('tokened load never flashes Complete before beat 1', async ({ page }) => {
  const token = 'test-155-noflash-' + Date.now();
  const seen: string[] = [];
  await page.exposeFunction('__chip', (t: string) => seen.push(t));
  await page.goto(`/viewer.html?token=${token}`);
  await page.evaluate(() => {
    new MutationObserver((muts) => {
      for (const m of muts) {
        const el = m.target as HTMLElement;
        // @ts-expect-error test hook
        window.__chip(el.textContent ?? '');
      }
    }).observe(document.documentElement, { subtree: true, characterData: true, childList: true });
  });
  await page.waitForTimeout(1500);
  await page.evaluate(([t]) => {
    window.postMessage(
      { type: 'CODECOACH_ANIMATION', token: t, animation: { title: 't', steps: [{ narration: 'a' }] } },
      '*',
    );
  }, [token]);
  await page.waitForTimeout(3000);
  expect(seen.filter((s) => s === 'Complete').length).toBeLessThanOrEqual(1);
  expect(seen[0]).not.toBe('Complete');
});
```

- [ ] **Step 2: Verify `onDurationChanged` fires once with the real length** (not demo 932 frames then a jump); keep the `MAX_TIMELINE_SECONDS = 120` defensive cap in `timelineMaxFrames`.
- [ ] **Step 3: Run lint + typecheck + related suite**; fix hook failures, do not bypass.
- [ ] **Step 4: Commit**

```bash
git add motion-canvas-lab/src/viewer-player.ts motion-canvas-lab/tests/viewer-duration.spec.ts
git commit -m "fix(155): harden scrubber to real duration, drop demo-pass flash"
```
