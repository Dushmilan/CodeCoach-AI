import { test, expect } from '@playwright/test';

test.describe('Performance', () => {
  test('homepage loads within acceptable time', async ({ page }) => {
    const start = Date.now();
    await page.goto('/');
    await expect(page.locator('header')).toBeVisible({ timeout: 15000 });
    const loadTime = Date.now() - start;
    expect(loadTime).toBeLessThan(15000);
  });

  test('learn page loads within acceptable time', async ({ page }) => {
    const start = Date.now();
    await page.goto('/learn');
    await expect(page.getByText('Learning Paths')).toBeVisible({ timeout: 15000 });
    const loadTime = Date.now() - start;
    expect(loadTime).toBeLessThan(15000);
  });
});
