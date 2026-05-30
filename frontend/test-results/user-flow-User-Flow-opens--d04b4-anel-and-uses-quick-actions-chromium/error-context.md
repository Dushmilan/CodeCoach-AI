# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: user-flow.spec.ts >> User Flow >> opens AI coaching panel and uses quick actions
- Location: e2e\user-flow.spec.ts:19:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const dismissOnboarding = async (page: import('@playwright/test').Page) => {
  4  |   await page.evaluate(() => localStorage.setItem('onboarding-done', 'true'));
  5  |   await page.reload();
  6  | };
  7  | 
  8  | test.describe('User Flow', () => {
  9  |   test('switches language in code editor', async ({ page }) => {
  10 |     await page.goto('/');
  11 |     await dismissOnboarding(page);
  12 |     await page.waitForSelector('text=Problems');
  13 | 
  14 |     const languageSelect = page.locator('select').first();
  15 |     await languageSelect.selectOption('javascript');
  16 |     await expect(languageSelect).toHaveValue('javascript');
  17 |   });
  18 | 
  19 |   test('opens AI coaching panel and uses quick actions', async ({ page }) => {
> 20 |     await page.goto('/');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  21 |     await dismissOnboarding(page);
  22 |     await page.waitForSelector('text=AI Coach');
  23 | 
  24 |     await expect(page.getByRole('button', { name: /hint/i })).toBeVisible();
  25 |     await expect(page.getByRole('button', { name: /review/i })).toBeVisible();
  26 |     await expect(page.getByRole('button', { name: /explain/i })).toBeVisible();
  27 |     await expect(page.getByRole('button', { name: /debug/i })).toBeVisible();
  28 |   });
  29 | 
  30 |   test('types in the chat input', async ({ page }) => {
  31 |     await page.goto('/');
  32 |     await dismissOnboarding(page);
  33 |     await page.waitForSelector('text=AI Coach');
  34 | 
  35 |     const chatInput = page.getByPlaceholder('Ask a question or describe your approach...');
  36 |     await chatInput.fill('How does recursion work?');
  37 |     await expect(chatInput).toHaveValue('How does recursion work?');
  38 |   });
  39 | 
  40 |   test('sidebar has filter controls', async ({ page }) => {
  41 |     await page.goto('/');
  42 |     await dismissOnboarding(page);
  43 |     await page.waitForSelector('text=Problems');
  44 |     await expect(page.getByRole('combobox').first()).toBeVisible();
  45 |   });
  46 | 
  47 |   test('code editor panel is visible', async ({ page }) => {
  48 |     await page.goto('/');
  49 |     await dismissOnboarding(page);
  50 |     await page.waitForSelector('text=Problems');
  51 |     await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
  52 |   });
  53 | });
  54 | 
```