import { expect, test, type Frame, type Page } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

const password = 'TestPass123!';

// A generic declarative scene with real shapes (rects, text, a pointer
// polygon) plus motion. The launcher posts this to the real chrome-less
// Motion Canvas viewer served by the lab dev server on localhost:9000
// (started by the Playwright webServer entry).
const genericAnimation = {
  title: 'Searching for 4',
  data: { values: [5, 1, 2, 3, 4, 6], target: 4 },
  steps: [
    {
      narration: '5 is not the target.',
      shapes: [
        {
          id: 'cell_0',
          type: 'rect',
          x: -240,
          y: 0,
          width: 88,
          height: 88,
          radius: 12,
          fill: '#1e293b',
          stroke: '#334155',
          text: '5',
        },
        {
          id: 'val_0',
          type: 'text',
          x: -240,
          y: 0,
          text: '5',
          fontSize: 34,
          fill: '#94a3b8',
        },
        {
          id: 'ptr',
          type: 'polygon',
          points: [
            [-12, -30],
            [0, -60],
            [12, -30],
          ],
          x: -240,
          y: -80,
          fill: '#facc15',
        },
      ],
      motion: [
        { target: 'cell_0', op: 'appear', duration: 0.3 },
        { target: 'val_0', op: 'appear', duration: 0.3 },
        { target: 'ptr', op: 'appear', duration: 0.3 },
      ],
    },
    {
      narration: 'Moving the pointer along.',
      motion: [{ target: 'ptr', op: 'move', to: [0, -80], duration: 0.5 }],
    },
    {
      narration: 'Found the target 4 at index 4.',
      shapes: [
        {
          id: 'cell_4',
          type: 'rect',
          x: 240,
          y: 0,
          width: 88,
          height: 88,
          radius: 12,
          fill: '#14532d',
          stroke: '#22c55e',
        },
        {
          id: 'val_4',
          type: 'text',
          x: 240,
          y: 0,
          text: '4',
          fontSize: 34,
          fill: '#ffffff',
        },
      ],
      motion: [
        { target: 'cell_4', op: 'appear', duration: 0.3 },
        { target: 'val_4', op: 'appear', duration: 0.3 },
        { target: 'ptr', op: 'move', to: [240, -80], duration: 0.5 },
      ],
    },
  ],
};

async function register(page: Page) {
  const ts = Date.now();
  const username = `render${ts}`;
  const email = `render${ts}@test.com`;
  await page.goto('/register');
  await page.getByLabel(/username/i).fill(username);
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /create account|register/i }).click();
  await expect(page).toHaveURL('/');
  return { username, email };
}

async function mockPremiumAndAnimate(page: Page, username: string, email: string) {
  await page.route('**/api/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'e2e-render-user',
        username,
        email,
        created_at: new Date().toISOString(),
        is_active: true,
        role: 'user',
        plan: 'premium',
      }),
    }),
  );

  await page.route('**/api/coach/animate', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ animation: genericAnimation }),
    });
  });
}

async function countPixelsNear(frame: Frame, hex: string): Promise<number> {
  return frame.evaluate(
    async (color: string) => {
      const canvas = document.querySelector<HTMLCanvasElement>('#stage-canvas');
      if (!canvas) return 0;
      const ctx = canvas.getContext('2d');
      if (!ctx) return 0;
      const { data } = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const [r, g, b] = [
        parseInt(color.slice(1, 3), 16),
        parseInt(color.slice(3, 5), 16),
        parseInt(color.slice(5, 7), 16),
      ];
      let count = 0;
      for (let i = 0; i < data.length; i += 4) {
        if (
          Math.abs(data[i] - r) < 16 &&
          Math.abs(data[i + 1] - g) < 16 &&
          Math.abs(data[i + 2] - b) < 16
        ) {
          count++;
        }
      }
      return count;
    },
    hex,
  );
}

// Mean x of pixels near `hex` — used to prove the pointer physically moves
// left→right across the timeline instead of sitting still.
async function meanXOfPixelsNear(frame: Frame, hex: string): Promise<number> {
  return frame.evaluate(
    async (color: string) => {
      const canvas = document.querySelector<HTMLCanvasElement>('#stage-canvas');
      if (!canvas) return 0;
      const ctx = canvas.getContext('2d');
      if (!ctx) return 0;
      const { data, width } = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const [r, g, b] = [
        parseInt(color.slice(1, 3), 16),
        parseInt(color.slice(3, 5), 16),
        parseInt(color.slice(5, 7), 16),
      ];
      let totalX = 0;
      let count = 0;
      for (let y = 0; y < canvas.height; y++) {
        for (let x = 0; x < width; x++) {
          const i = (y * width + x) * 4;
          if (
            Math.abs(data[i] - r) < 16 &&
            Math.abs(data[i + 1] - g) < 16 &&
            Math.abs(data[i + 2] - b) < 16
          ) {
            totalX += x;
            count++;
          }
        }
      }
      return count === 0 ? -1 : totalX / count;
    },
    hex,
  );
}

test.describe('Viewer rendering', () => {
  test('the Motion Canvas viewer paints the generic scene (shapes + motion)', async ({
    page,
  }) => {
    const { username, email } = await register(page);
    await mockPremiumAndAnimate(page, username, email);
    await dismissOnboarding(page);

    await page.goto('/problems');
    await page.waitForSelector('tbody tr');
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/);

    const animate = page.getByRole('button', { name: 'Animate solution' });
    await expect(animate).toBeVisible({ timeout: 15000 });
    await expect(animate).toBeEnabled({ timeout: 15000 });
    await animate.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 15000 });
    const iframe = dialog.getByTitle('Animation viewer');
    await expect(iframe).toBeVisible({ timeout: 15000 });

    // The scene generator registers its message bridge at module load and the
    // launcher posts on iframe load; give the lab a moment to boot in CI.
    const viewerFrame = () =>
      page.frames().find((f) => f.url().includes('viewer.html'));
    await expect
      .poll(() => viewerFrame()?.url() ?? '', { timeout: 20000 })
      .toContain('viewer.html');

    // The cell/pointer shapes must actually paint: assert at least one pixel
    // of the pointer yellow (#facc15) that only exists in the generic scene,
    // proving the payload reached the renderer and produced vector output —
    // not just a title card.
    const frame = viewerFrame()!;
    await expect
      .poll(() => countPixelsNear(frame, '#facc15'), { timeout: 25000 })
      .toBeGreaterThan(50);

    // Cell values must be visible: cell_0 carries text "5" rendered inside the
    // rect — light text pixels (#e2e8f0) prove values paint, not blank boxes.
    await expect
      .poll(() => countPixelsNear(frame, '#e2e8f0'), { timeout: 15000 })
      .toBeGreaterThan(20);

    // The pointer must actually MOVE: its mean x must cross into the right
    // half of the canvas — it starts over cell_0 (left) and step 2 moves it to
    // cell_4 (right). A static scene (the regression we're fixing) would never
    // leave the left side.
    await expect
      .poll(() => meanXOfPixelsNear(frame, '#facc15'), { timeout: 25000 })
      .toBeGreaterThan(1100);
  });
});
