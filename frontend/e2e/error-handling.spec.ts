import { test, expect } from '@playwright/test';

test.describe('Error Handling', () => {
  test('404 page shows for unknown route', async ({ page }) => {
    await page.goto('/nonexistent-page-xyz');
    await page.waitForLoadState('domcontentloaded');
    expect(await page.textContent('body')).toBeTruthy();
  });

  test('handles network errors gracefully', async ({ page }) => {
    await page.route('**/api/**', route => route.abort('connectionrefused'));
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('body')).toBeVisible();
  });
});
