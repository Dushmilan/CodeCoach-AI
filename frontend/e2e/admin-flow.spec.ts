import { test, expect } from '@playwright/test';
import { loginAs } from './helpers/auth';

test.describe('Admin Flow', () => {
  test('login page loads and shows form', async ({ page }) => {
    await page.goto('/admin/login');
    await expect(page.getByRole('main').getByRole('button', { name: /sign in/i })).toBeVisible({ timeout: 15000 });
  });

  test('admin login redirects to dashboard', async ({ page }) => {
    await page.goto('/admin/login');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill('admin');
    await page.getByLabel(/password/i).fill('admin123');
    await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('dashboard shows stats cards', async ({ page }) => {
    await page.goto('/admin/login');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill('admin');
    await page.getByLabel(/password/i).fill('admin123');
    await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
    await expect(page.getByText(/welcome back/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('sidebar navigation works', async ({ page }) => {
    await page.goto('/admin/login');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill('admin');
    await page.getByLabel(/password/i).fill('admin123');
    await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('**/admin/dashboard', { timeout: 15000 });

    await page.getByRole('link', { name: /users/i }).click();
    await page.waitForURL('**/admin/users');
    await expect(page.getByRole('heading', { name: /users/i })).toBeVisible();

    await page.getByRole('link', { name: /questions/i }).click();
    await page.waitForURL('**/admin/questions');
    await expect(page.getByRole('heading', { name: /questions/i })).toBeVisible();
  });

  test('unauthenticated access shows access denied', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await expect(page.getByText(/access denied/i)).toBeVisible({ timeout: 15000 });
  });
});
