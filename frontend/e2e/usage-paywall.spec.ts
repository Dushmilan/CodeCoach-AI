import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

// D5 (Issue #202): the AI paywall path — a 429 from /api/coach/ must surface
// the daily-limit error + toast instead of a generic failure.
test.describe('Usage paywall', () => {
  test('coach 429 shows the daily-limit message and toast', async ({ page }) => {
    const ts = Date.now();
    await page.goto('/register');
    await page.getByLabel(/username/i).fill('paywall' + ts);
    await page.getByLabel(/email/i).fill('paywall' + ts + '@test.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /create account|register/i }).click();
    await expect(page).toHaveURL('/');

    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });

    const chatInput = page.getByPlaceholder('Ask a question or describe your approach...');
    await expect(chatInput).toBeVisible({ timeout: 15000 });

    await page.route('**/api/coach/', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Daily AI message limit reached' }),
      });
    });

    await chatInput.fill('Give me a hint for this problem');
    await chatInput.press('Enter');

    await expect(
      page.getByText(/you've reached your daily ai message limit/i).first()
    ).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/daily ai message limit reached/i).first()).toBeVisible({
      timeout: 15000,
    });
  });
});
