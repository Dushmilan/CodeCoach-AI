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
