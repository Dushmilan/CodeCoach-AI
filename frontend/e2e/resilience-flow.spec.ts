import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Backend-down UX', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/**', (route) => route.abort('failed'));
  });

  test('problems list shows an inline error instead of hanging', async ({
    page,
  }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await expect(page.getByText(/request failed|failed to/i).first()).toBeVisible(
      { timeout: 20000 },
    );
  });

  test('problem detail shows error copy with a way back', async ({ page }) => {
    await page.goto('/problems/two-sum');
    await dismissOnboarding(page);
    await expect(page.getByText(/request failed|failed to/i).first()).toBeVisible(
      { timeout: 20000 },
    );
    await expect(
      page.getByRole('link', { name: /back to problems/i }),
    ).toBeVisible({ timeout: 15000 });
  });

  test('login stays on page with an inline error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('mia');
    await page.getByLabel(/password/i).fill('student123');
    await page
      .getByRole('main')
      .getByRole('button', { name: /sign in/i })
      .click();
    await expect(page).toHaveURL(/\/login/, { timeout: 15000 });
    await expect(page.getByText(/request failed|failed to|timeout/i).first()).toBeVisible(
      { timeout: 20000 },
    );
  });
});
