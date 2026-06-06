import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Accessibility', () => {
  test('homepage has semantic header', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.locator('header')).toBeVisible();
  });

  test('learn page has accessible navigation', async ({ page }) => {
    await page.goto('/learn');
    await page.waitForLoadState('networkidle');
    const navLinks = page.locator('header').getByRole('link');
    const count = await navLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('page elements have descriptive text', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
  });
});
