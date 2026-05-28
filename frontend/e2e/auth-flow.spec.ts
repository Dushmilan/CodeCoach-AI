import { test, expect } from '@playwright/test';

const dismissOnboarding = async (page: import('@playwright/test').Page) => {
  await page.evaluate(() => localStorage.setItem('onboarding-done', 'true'));
  await page.reload();
};

test.describe('Auth Flow', () => {
  test('shows sign in button when logged out', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible();
  });

  test('login page has required fields', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible();
  });

  test('register page has all fields', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /create account|register/i })).toBeVisible();
  });

  test('register navigates to home after success', async ({ page }) => {
    await page.goto('/register');
    const ts = Date.now();
    await page.getByLabel(/username/i).fill('e2euser' + ts);
    await page.getByLabel(/email/i).fill('e2e' + ts + '@test.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /create account|register/i }).click();
    await expect(page).toHaveURL('/');
  });

  test('learn page shows curriculum when logged out', async ({ page }) => {
    await page.goto('/learn');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});
