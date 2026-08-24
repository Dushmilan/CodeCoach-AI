import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('Homepage', () => {
  test('loads the landing page shell', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.locator('header')).toBeVisible();
    await expect(page.getByRole('heading', { name: /a free ai-powered/i })).toBeVisible();
  });

  test('header nav links are visible', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.locator('header').getByRole('link', { name: 'Problems' })).toBeVisible();
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  });

  test('hero CTAs link to problems and curriculum', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.getByRole('link', { name: /start practicing/i }).first()).toBeVisible();
    await expect(page.getByRole('link', { name: /view curriculum/i }).first()).toBeVisible();
  });

  test('settings modal opens and closes', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.getByRole('button', { name: /settings/i }).first().click();
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
  });

  test('features section is visible', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.getByRole('heading', { name: /why codecoach ai/i })).toBeVisible();
  });
});
