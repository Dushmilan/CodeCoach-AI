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
  // Payload-shape math: 18 narration-only steps (no `operation` field) render
  // via renderGenericScene (~0.85s/step -> ~17s total: 0.8 intro + 18x0.85 +
  // 1.4 outro ~= 17.5s, observed `0:17`), not renderNarrationTimeline
  // (~1.6s/step -> ~30s) which the brief's `~0:30` estimate assumed.
  // Floor is >=0:16: strictly above the untokened demo total (0:15), so time
  // still discriminates demo from real branch. Chip 18/18 (unreachable on
  // the 3-step demo branch) is the primary discriminator.
  expect(time).toMatch(/0:(1[6-9]|[2-5]\d)|1:/);
});

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

test('tokened scrubber binds to the real timeline once (no demo-length jump)', async ({ page }) => {
  const token = 'test-155-duration-' + Date.now();
  await page.goto(`/viewer.html?token=${token}`);
  await page.evaluate(() => {
    // @ts-expect-error test hook
    window.__maxima = [];
    const scrubber = () => document.getElementById('viewer-scrubber') as HTMLInputElement | null;
    const poll = window.setInterval(() => {
      const el = scrubber();
      if (el) {
        // @ts-expect-error test hook
        const arr = window.__maxima as number[];
        const v = Number(el.max);
        if (arr[arr.length - 1] !== v) arr.push(v);
      }
    }, 100);
    // @ts-expect-error test hook
    window.__stopMaxima = () => window.clearInterval(poll);
  });
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
  const distinct: number[] = await page.evaluate(() => {
    // @ts-expect-error test hook
    window.__stopMaxima();
    // @ts-expect-error test hook
    return window.__maxima as number[];
  });
  // Scrubber max must stay bound to the real timeline: at most one transient
  // besides the real value (default "100" before first setProgress), never a
  // demo-length value followed by a jump to the real length.
  const real = distinct.filter((v) => v !== 100);
  expect(real.length).toBeGreaterThan(0);
  expect(new Set(real).size).toBeLessThanOrEqual(2);
  expect(real[real.length - 1]).toBeGreaterThan(100);
  // The bound length is the real ~17s branch: strictly above the untokened
  // demo total, within the MAX_TIMELINE_SECONDS = 120 defensive cap.
  const durationTime = (await page.locator('#viewer-time').textContent()) ?? '';
  const total = durationTime.split('/')[1]?.trim() ?? '';
  const m = total.match(/(\d+):(\d\d)/);
  expect(m).not.toBeNull();
  const totalSeconds = Number(m![1]) * 60 + Number(m![2]);
  expect(totalSeconds).toBeGreaterThanOrEqual(16);
  expect(totalSeconds).toBeLessThanOrEqual(120);
});

test('untokened demo path still plays the built-in demo', async ({ page }) => {
  await page.goto('/viewer.html');
  await expect(page.locator('#viewer-step-chip')).toContainText('3 / 3', { timeout: 45000 });
  const time = (await page.locator('#viewer-time').textContent()) ?? '';
  expect(time).toMatch(/0:1\d/);
});

test('tokened error payload surfaces Generation failed', async ({ page }) => {
  const token = 'test-155-error-' + Date.now();
  await page.goto(`/viewer.html?token=${token}`);
  await page.waitForTimeout(1500);
  await page.evaluate(([t]) => {
    window.postMessage({ type: 'CODECOACH_ANIMATION_ERROR', token: t, message: 'boom-155' }, '*');
  }, [token]);
  await expect(page.locator('#viewer-narration')).toContainText('boom-155', { timeout: 30000 });
  await expect(page.locator('#viewer-step-chip')).toContainText('Generation failed', { timeout: 30000 });
});
