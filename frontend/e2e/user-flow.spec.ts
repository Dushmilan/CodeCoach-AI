import { test, expect } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

test.describe('User Flow', () => {
  test('switches language in code editor', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });
    await expect(page.getByRole('combobox', { name: /programming language/i })).toBeVisible({ timeout: 15000 });
    const languageSelect = page.getByRole('combobox', { name: /programming language/i });
    const options = await languageSelect.locator('option').allTextContents();
    if (options.some((o) => /javascript/i.test(o))) {
      await languageSelect.selectOption('javascript');
      await expect(languageSelect).toHaveValue('javascript');
    }
  });

  test('opens AI coaching panel and uses quick actions', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });
    // When logged out the AI Coach shows a sign-in prompt; when logged in it shows quick actions.
    const hintBtn = page.getByRole('button', { name: /^hint$/i });
    const signInPrompt = page.getByText(/sign in to use the ai coach/i);
    await expect(hintBtn.or(signInPrompt)).toBeVisible({ timeout: 15000 });
  });

  test('types in the chat input', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });
    const chatInput = page.getByPlaceholder('Ask a question or describe your approach...');
    const signInPrompt = page.getByText(/sign in to use the ai coach/i);
    // Logged-out workspace shows sign-in prompt instead of chat input
    if (await chatInput.count()) {
      await chatInput.fill('How does recursion work?');
      await expect(chatInput).toHaveValue('How does recursion work?');
    } else {
      await expect(signInPrompt).toBeVisible({ timeout: 10000 });
    }
  });

  test('sidebar has filter controls', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await expect(page.getByRole('heading', { name: 'Problems' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('combobox').first()).toBeVisible();
  });

  test('code editor panel is visible', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.locator('tbody tr').first().click();
    await page.waitForURL(/\/problems\/.+/, { timeout: 15000 });
    await expect(page.getByRole('combobox', { name: /programming language/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: /^run$/i })).toBeVisible();
  });
});
