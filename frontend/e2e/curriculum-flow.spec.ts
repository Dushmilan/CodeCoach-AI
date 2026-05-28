import { test, expect } from '@playwright/test';

test.describe('Curriculum Flow', () => {
  test('learn page shows nav link in header', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  });

  test('learn page loads with heading', async ({ page }) => {
    await page.goto('/learn');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Learning Paths')).toBeVisible();
  });

  test('learn page shows auth-required state or course cards', async ({ page }) => {
    await page.goto('/learn');
    await page.waitForLoadState('networkidle');
    const body = page.locator('body');
    await expect(body).toContainText(/Learning Paths|Sign in|log in|courses/i);
  });

  test('header has learn link on all pages', async ({ page }) => {
    await page.goto('/learn');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
    await page.goto('/');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  });
});
