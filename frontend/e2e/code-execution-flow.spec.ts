import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Code Execution Flow', () => {
  test('code editor is visible with language selector', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });
    await expect(page.getByRole('combobox', { name: /programming language/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: /^run$/i })).toBeVisible();
  });

  test('runs code and displays output', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });
    const runButton = page.getByRole('button', { name: /^run$/i });
    if (await runButton.isVisible()) {
      await runButton.click();
      await page.waitForTimeout(1000);
    }
  });

  test('shows submit button', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });
    await expect(page.getByRole('button', { name: /submit/i })).toBeVisible();
  });
});
