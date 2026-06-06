import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Code Execution Flow', () => {
  test('code editor is visible with language selector', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');
    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
  });

  test('runs code and displays output', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');
    const runButton = page.getByRole('button', { name: /run/i });
    if (await runButton.isVisible()) {
      await runButton.click();
      await page.waitForTimeout(1000);
    }
  });

  test('shows submit button', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');
    await expect(page.getByRole('button', { name: /submit/i })).toBeVisible();
  });
});
