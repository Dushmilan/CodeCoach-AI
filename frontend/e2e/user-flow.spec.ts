import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('User Flow', () => {
  test('switches language in code editor', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');

    const languageSelect = page.locator('select').first();
    await languageSelect.selectOption('javascript');
    await expect(languageSelect).toHaveValue('javascript');
  });

  test('opens AI coaching panel and uses quick actions', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=AI Coach');

    await expect(page.getByRole('button', { name: /hint/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /review/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /explain/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /debug/i })).toBeVisible();
  });

  test('types in the chat input', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=AI Coach');

    const chatInput = page.getByPlaceholder('Ask a question or describe your approach...');
    await chatInput.fill('How does recursion work?');
    await expect(chatInput).toHaveValue('How does recursion work?');
  });

  test('sidebar has filter controls', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');
    await expect(page.getByRole('combobox').first()).toBeVisible();
  });

  test('code editor panel is visible', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    await page.waitForSelector('text=Problems');
    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
  });
});
