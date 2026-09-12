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
  // Verified: 18 narration-only steps render via renderGenericScene
  // (~0.85s/step -> ~17s total), not the narration timeline (~30s).
  // Chip 18/18 (unreachable on the 3-step demo branch) is the discriminator.
  expect(time).toMatch(/0:(1[5-9]|[2-5]\d)|1:/);
});
