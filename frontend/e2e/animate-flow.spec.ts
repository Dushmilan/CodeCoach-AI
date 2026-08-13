import { test, expect, Page } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

const password = 'TestPass123!';

const animateResponse = {
  animation: {
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
  },
};

const VIEWER_STUB_HTML = `<!doctype html><html><body><script>
window.addEventListener('message', (e) => {
  if (e.data && e.data.type && e.data.token) {
    parent.postMessage({ __codecoach_animate: e.data }, '*');
  }
});
<\/script></body></html>`;

async function register(page: Page) {
  const ts = Date.now();
  const username = `animate${ts}`;
  const email = `animate${ts}@test.com`;
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
        id: 'e2e-animate-user',
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
      body: JSON.stringify(animateResponse),
    });
  });
}

/**
 * Serve a stub for the chrome-less lab viewer (viewer.html) and relay the
 * postMessage handshake payloads back to the test window so the test can
 * assert exactly what the launcher posts to the viewer iframe.
 */
async function stubViewerIframe(page: Page) {
  await page.route(/^http:\/\/localhost:9000\//, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: VIEWER_STUB_HTML,
    }),
  );
  await page.addInitScript(() => {
    (window as any).__animateMessages = [];
    window.addEventListener('message', (event: MessageEvent) => {
      const data = event.data as { __codecoach_animate?: unknown } | null;
      if (data && data.__codecoach_animate) {
        (window as any).__animateMessages.push(data.__codecoach_animate);
      }
    });
  });
}

async function openFirstProblemWorkspace(page: Page) {
  await page.goto('/problems');
  await page.waitForSelector('tbody tr');
  await page.locator('tbody tr').first().click();
  await page.waitForURL(/\/problems\/.+/);
}

test.describe('AI Animate flow', () => {
  test.describe.configure({ mode: 'serial' });

  test('opens an in-app viewer modal and posts the animation payload (no chat call)', async ({
    page,
  }) => {
    const { username, email } = await register(page);
    await stubViewerIframe(page);
    await mockPremiumAndAnimate(page, username, email);
    await dismissOnboarding(page);
    await openFirstProblemWorkspace(page);

    const animate = page.getByRole('button', { name: 'Animate solution' });
    await expect(animate).toBeVisible({ timeout: 15000 });
    await expect(animate).toBeEnabled({ timeout: 15000 });
    await animate.click();

    // The animation opens in an in-app modal (no new window) with a one-time
    // token in the chrome-less viewer iframe URL.
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 15000 });
    const iframe = dialog.getByTitle('Animation viewer');
    await expect(iframe).toBeVisible();
    await expect(iframe).toHaveAttribute('src', /viewer\.html\?token=/);
    const src = await iframe.getAttribute('src');
    const token = new URL(src!).searchParams.get('token');
    expect(token).toBeTruthy();

    // The validated animation is posted to the viewer with the same token.
    await expect
      .poll(() =>
        page.evaluate(
          () => (window as any).__animateMessages?.[0]?.type as string | undefined,
        ),
      )
      .toBe('CODECOACH_ANIMATION');

    const handshake = await page.evaluate(
      () => (window as any).__animateMessages?.[0],
    );
    expect(handshake.token).toBe(token);
    expect(handshake.animation.title).toBe('Searching for 4');
    expect(handshake.animation.data.target).toBe(4);
    expect(handshake.animation.steps[0].motion[0].op).toBe('appear');
    expect(handshake.animation.steps[0].shapes[0].id).toBe('cell_0');

    // The AI chat panel must not render the animation as a chat message.
    await expect(
      page.getByText('Searching for 4', { exact: true }),
    ).not.toBeVisible();
    await expect(
      page.getByText('Found the target 4 at index 4.', { exact: true }),
    ).not.toBeVisible();
  });

  test('posts an error message to the viewer when generation fails', async ({
    page,
  }) => {
    const { username, email } = await register(page);
    await stubViewerIframe(page);
    await page.route('**/api/coach/animate', async (route) => {
      await route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Failed to generate animation' }),
      });
    });
    await page.route('**/api/auth/me', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'e2e-animate-user',
          username,
          email,
          created_at: new Date().toISOString(),
          is_active: true,
          role: 'user',
          plan: 'premium',
        }),
      }),
    );
    await dismissOnboarding(page);
    await openFirstProblemWorkspace(page);

    const animate = page.getByRole('button', { name: 'Animate solution' });
    await expect(animate).toBeVisible({ timeout: 15000 });
    await expect(animate).toBeEnabled({ timeout: 15000 });
    await animate.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 15000 });
    await expect(dialog.getByRole('alert')).toBeVisible();

    await expect
      .poll(() =>
        page.evaluate(
          () => (window as any).__animateMessages?.[0]?.type as string | undefined,
        ),
      )
      .toBe('CODECOACH_ANIMATION_ERROR');
  });

  test('the chat panel no longer offers Animate', async ({ page }) => {
    const { username, email } = await register(page);
    await mockPremiumAndAnimate(page, username, email);
    await dismissOnboarding(page);
    await openFirstProblemWorkspace(page);

    // The AI Coach panel still shows its regular quick actions...
    await expect(
      page.getByRole('heading', { name: 'AI COACH', exact: true }),
    ).toBeVisible({ timeout: 15000 });
    await expect(
      page.getByRole('button', { name: 'Hint', exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Explain', exact: true }),
    ).toBeVisible();

    // ...but Animate is no longer a chat action. The only Animate button is
    // the standalone launcher, whose accessible name is "Animate solution".
    await expect(
      page.getByRole('button', { name: 'Animate', exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByRole('button', { name: 'Animate solution' }),
    ).toBeVisible();
  });
});
