import { Page, expect } from '@playwright/test';

export async function loginAs(page: Page, username: string, password: string) {
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');
  await page.getByLabel(/username/i).fill(username);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL('/', { timeout: 15000 });
}

export async function dismissOnboarding(page: Page) {
  await page.evaluate(() => localStorage.setItem('onboarding-done', 'true'));
  await page.reload();
  await page.waitForLoadState('domcontentloaded');
}
