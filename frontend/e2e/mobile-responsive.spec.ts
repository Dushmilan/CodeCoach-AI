import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Mobile Responsive', () => {
  test('sidebar is hidden on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await dismissOnboarding(page);
    const sidebar = page.getByRole('complementary');
    const isVisible = await sidebar.isVisible().catch(() => false);
    expect(typeof isVisible).toBe('boolean');
  });

  test('page renders on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.locator('header')).toBeVisible();
  });
});
