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

  test('header has learn link on all pages', async ({ page }) => {
    await page.goto('/learn');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
    await page.goto('/');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  });

  test('course detail page shows not found for non-existent course', async ({ page }) => {
    await page.goto('/learn/nonexistent-course');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('not found')).toBeVisible();
  });
});
