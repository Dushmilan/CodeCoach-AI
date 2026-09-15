import { test, expect, Page } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

const password = 'TestPass123!';

// Generic declarative scene (no legacy `type`): the A1 viewer must render it
// with the cinematic SVG renderer + scrub player, not fallback text.
const scrubAnimation = {
  title: 'Bubble Sort',
  data: { family: 'array' },
  steps: [
    {
      narration: 'Compare arr[0]=5 vs arr[1]=3 — 5 > 3, keep scanning.',
      shapes: [
        { id: 'cell_0', type: 'rect', x: -50, y: 0, width: 88, height: 88, fill: '#1e293b', stroke: '#334155' },
        { id: 'val_0', type: 'text', x: -50, y: 0, text: '5', fontSize: 28, fill: '#e2e8f0' },
      ],
      motion: [{ target: 'cell_0', op: 'fill', to: '#1d4ed8', duration: 0.35 }],
      camera: { action: 'focus', region: [0, 1] },
    },
    {
      narration: 'Swap arr[0] and arr[1].',
      shapes: [
        { id: 'cell_0', type: 'rect', x: -50, y: 0, width: 88, height: 88, fill: '#1d4ed8', stroke: '#3b82f6' },
        { id: 'val_0', type: 'text', x: -50, y: 0, text: '5', fontSize: 28, fill: '#e2e8f0' },
      ],
      motion: [{ target: 'cell_0', op: 'move', to: [50, 0], duration: 0.4 }],
    },
    {
      narration: 'Complexity O(n²) time, O(1) space',
      shapes: [],
      motion: [],
      badge: { time: 'O(n²)', space: 'O(1)' },
    },
  ],
};

const coachResponse = {
  response: 'Here is how bubble sort behaves on your input.',
  structured: {
    summary: 'Bubble sort compares adjacent pairs and swaps them.',
    hints: ['Watch the highlighted pair each beat.'],
    code_review: null,
    complexity_analysis: 'Quadratic time, constant space.',
    suggestions: [],
    edge_cases: [],
    explanation: null,
    debug_help: null,
    animation: scrubAnimation,
  },
};

async function register(page: Page) {
  const ts = Date.now();
  const username = `scrub${ts}`;
  const email = `scrub${ts}@test.com`;
  await page.goto('/register');
  await page.getByLabel(/username/i).fill(username);
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /create account|register/i }).click();
  await expect(page).toHaveURL('/');
  return { username, email };
}

async function mockCoach(page: Page, username: string, email: string) {
  await page.route('**/api/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'e2e-scrub-user',
        username,
        email,
        created_at: new Date().toISOString(),
        is_active: true,
        role: 'user',
        plan: 'premium',
      }),
    }),
  );
  await page.route('**/api/coach/warm', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok', warmed: true, ttl: 60 }),
    }),
  );
  await page.route(/\/api\/coach\/(\?.*)?$/, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(coachResponse),
    }),
  );
}

async function openFirstProblemWorkspace(page: Page) {
  await page.goto('/problems');
  await page.waitForSelector('tbody tr');
  await page.locator('tbody tr').first().click();
  await page.waitForURL(/\/problems\/.+/);
}

async function openChat(page: Page) {
  const drawerButton = page.getByRole('button', { name: 'Open AI Panel' });
  if (await drawerButton.isVisible().catch(() => false)) {
    await drawerButton.click();
  }
  await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible({ timeout: 15000 });
}

test.describe('Animation scrub player', () => {
  test('renders generic scenes cinematically with scrub, keyboard, and final-beat badge', async ({
    page,
  }) => {
    const { username, email } = await register(page);
    await mockCoach(page, username, email);
    await dismissOnboarding(page);
    await openFirstProblemWorkspace(page);
    await openChat(page);

    await page.getByPlaceholder(/ask a question/i).fill('Explain bubble sort');
    await page.getByPlaceholder(/ask a question/i).press('Enter');

    const player = page.getByRole('region', { name: 'Animation player' });
    await expect(player).toBeVisible({ timeout: 15000 });

    // Cinematic SVG renderer (not fallback text): the scene paints an <svg>.
    await expect(player.getByRole('img', { name: /compare arr/i })).toBeVisible({ timeout: 15000 });
    await expect(player.getByText('Compare arr[0]=5 vs arr[1]=3', { exact: false })).toBeVisible();

    // Badge only lives on the final beat: hidden on the first beat.
    await expect(player.getByText('O(n²)', { exact: true })).toBeHidden();

    // Scrub slider jumps to the final beat: narration + badge appear.
    const slider = player.getByRole('slider', { name: /animation progress/i });
    await expect(slider).toBeVisible();
    await slider.fill('2');
    await expect(player.getByText('Complexity O(n²) time, O(1) space')).toBeVisible();
    await expect(player.getByText('O(n²)', { exact: true })).toBeVisible();
    await expect(player.getByText('O(1)', { exact: true })).toBeVisible();

    // Keyboard: arrows step back and forth between beats.
    await player.focus();
    await page.keyboard.press('ArrowLeft');
    await expect(player.getByText('Swap arr[0] and arr[1].')).toBeVisible();
    await expect(player.getByText('O(n²)', { exact: true })).toBeHidden();
    await page.keyboard.press('ArrowRight');
    await expect(player.getByText('Complexity O(n²) time, O(1) space')).toBeVisible();
  });
});
