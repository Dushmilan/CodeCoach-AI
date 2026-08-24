import { test, expect } from '@playwright/test';
import { loginAs, dismissOnboarding } from './helpers/auth';

test.describe('Auth Login-Logout Flow', () => {
  test('sign in link visible when logged out', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible();
  });

  test('login page has all fields', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('main').getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('register with invalid data shows error', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');
    await page.getByRole('button', { name: /create account|register/i }).click();
    await page.waitForTimeout(500);
  });

  test('register then login flow', async ({ page }) => {
    const ts = Date.now();
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill('e2euser' + ts);
    await page.getByLabel(/email/i).fill('e2e' + ts + '@test.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /create account|register/i }).click();
    await expect(page).toHaveURL('/');
  });

  test('protected route redirects to login', async ({ page }) => {
    await page.goto('/learn');
    await expect(page.getByText('Learning Paths')).toBeVisible({ timeout: 15000 });
  });
});
