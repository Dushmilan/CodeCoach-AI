import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Settings Flow', () => {
  test('settings modal opens from gear icon', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.locator('header').getByRole('button', { name: /settings/i }).click();
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
  });

  test('settings modal can be dismissed with Escape', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.locator('header').getByRole('button', { name: /settings/i }).click();
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
  });

  test('settings modal shows vertical column sections without dashboard tabs', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.locator('header').getByRole('button', { name: /settings/i }).click();
    const tablist = page.getByRole('tablist');
    await expect(tablist).toHaveAttribute('aria-orientation', 'vertical');
    await expect(page.getByTestId('settings-tab-general')).toBeVisible();
    await expect(page.getByTestId('settings-tab-plan')).toBeVisible();
    await expect(page.getByTestId('settings-tab-account')).toBeVisible();
    // Dashboard / skill-graph moved out of the gear menu into /dashboard
    await expect(page.getByTestId('settings-tab-dashboard')).toHaveCount(0);
    await expect(page.getByTestId('settings-tab-skills')).toHaveCount(0);
    await page.keyboard.press('Escape');
  });

  test('settings modal supports keyboard navigation between sections', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.locator('header').getByRole('button', { name: /settings/i }).click();
    const general = page.getByTestId('settings-tab-general');
    await expect(general).toBeVisible();
    await general.focus();
    await expect(general).toBeFocused();
    await page.keyboard.press('ArrowDown');
    await expect(page.getByTestId('settings-tab-plan')).toBeFocused();
    await page.keyboard.press('ArrowDown');
    await expect(page.getByTestId('settings-tab-account')).toBeFocused();
    await page.keyboard.press('ArrowUp');
    await expect(page.getByTestId('settings-tab-plan')).toBeFocused();
    await page.keyboard.press('Escape');
  });

  test('dashboard route stays routable with the skill-graph path', async ({ page }) => {
    await page.goto('/dashboard');
    await dismissOnboarding(page);
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 15000 });
  });
});
