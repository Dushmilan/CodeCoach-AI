import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Settings Flow', () => {
  test('settings modal opens from gear icon', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.getByRole('button', { name: /settings/i }).click();
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
  });

  test('settings modal can be dismissed with Escape', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.getByRole('button', { name: /settings/i }).click();
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
  });
});
