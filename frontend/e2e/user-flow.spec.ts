import { test, expect } from '@playwright/test';

test.describe('User Flow', () => {
  test('selects a question and switches to description view', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=Two Sum');

    await page.getByText('Two Sum').first().click();
    await page.getByText('Show Active Question').click();

    await expect(page.getByText('Back to list')).toBeVisible({ timeout: 5000 });
  });

  test('switches language in code editor', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=Problems');

    const languageSelect = page.locator('select').first();
    await languageSelect.selectOption('javascript');
    await expect(languageSelect).toHaveValue('javascript');
  });

  test('opens AI coaching panel and uses quick actions', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=AI Coach');

    await expect(page.getByRole('button', { name: /hint/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /review/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /explain/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /debug/i })).toBeVisible();
  });

  test('types in the chat input', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('text=AI Coach');

    const chatInput = page.getByPlaceholder('Ask a question or describe your approach...');
    await chatInput.fill('How does recursion work?');
    await expect(chatInput).toHaveValue('How does recursion work?');
  });

  test('full flow: browse, select, and interact', async ({ page }) => {
    await page.goto('/');

    await page.waitForSelector('text=Two Sum');
    await page.getByText('Two Sum').first().click();

    await page.waitForSelector('text=AI Coach');
    const chatInput = page.getByPlaceholder('Ask a question or describe your approach...');
    await chatInput.fill('Help me solve this');

    const sendButton = page.locator('button').filter({ has: page.locator('.lucide-send') });
    await expect(sendButton).toBeVisible();
  });
});
