import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
  test('loads the application shell', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('CodeCoach AI');
    await expect(page.locator('h2').filter({ hasText: 'Problems' })).toBeVisible();
  });

  test('sidebar shows questions', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=Problems');
    await expect(page.locator('text=Two Sum').first()).toBeVisible({ timeout: 10000 });
  });

  test('settings modal opens and closes', async ({ page }) => {
    await page.goto('/');
    await page.getByTitle('Settings').click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.locator('[role="dialog"] button:has-text("Cancel")').click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('sidebar can collapse', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Collapse sidebar').click();
    await expect(page.getByLabel('Expand sidebar')).toBeVisible();
  });

  test('view mode toggle switches to description mode', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=Two Sum');
    await page.getByText('Show Active Question').click();
    await expect(page.getByText('Show All Questions')).toBeVisible();
  });
});
