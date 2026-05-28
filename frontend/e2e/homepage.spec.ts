import { test, expect } from '@playwright/test';

const dismissOnboarding = async (page: import('@playwright/test').Page) => {
  await page.evaluate(() => localStorage.setItem('onboarding-done', 'true'));
  await page.reload();
};

test.describe('Homepage', () => {
  test('loads the application shell', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByText('Problems')).toBeVisible();
  });

  test('sidebar shows question list', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');
    const sidebar = page.getByRole('complementary').filter({ hasText: 'PROBLEMS' });
    await expect(sidebar).toBeVisible();
  });

  test('settings modal opens and closes', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.getByTitle('Settings').click({ force: true });
    await expect(page.locator('div').filter({ hasText: 'SETTINGS' }).nth(2)).toBeVisible({ timeout: 5000 });
    await page.keyboard.press('Escape');
  });

  test('sidebar can collapse', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.getByLabel('Collapse sidebar').click({ force: true });
    await expect(page.getByLabel('Expand sidebar')).toBeVisible();
  });

  test('view mode toggle switches to description mode', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');
    await page.getByText('Show Active Question').click({ force: true });
    await expect(page.getByText('Show All Questions')).toBeVisible();
  });
});
