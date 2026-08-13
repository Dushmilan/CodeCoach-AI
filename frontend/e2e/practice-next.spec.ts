import { test, expect } from '@playwright/test';

test.describe('Practice Next recommendations', () => {
  test('shows a sign-in prompt for anonymous users on /problems', async ({ page }) => {
    await page.goto('/problems');
    const panel = page.getByRole('region', { name: 'Practice next' });
    await expect(panel).toBeVisible();
    await expect(panel.getByText(/sign in to get personalized practice/i)).toBeVisible();
    await expect(panel.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login');
  });

  test('does not break the question browser for anonymous users', async ({ page }) => {
    await page.goto('/problems');
    await expect(page.getByRole('heading', { name: 'Problems' })).toBeVisible();
    await expect(page.getByLabel('Search questions')).toBeVisible();
  });
});
