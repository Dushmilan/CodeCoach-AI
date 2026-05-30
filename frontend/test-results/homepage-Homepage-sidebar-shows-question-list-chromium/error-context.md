# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: homepage.spec.ts >> Homepage >> sidebar shows question list
- Location: e2e\homepage.spec.ts:16:7

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
  8  | test.describe('Homepage', () => {
  9  |   test('loads the application shell', async ({ page }) => {
  10 |     await page.goto('/');
  11 |     await dismissOnboarding(page);
  12 |     await expect(page.locator('header')).toBeVisible();
  13 |     await expect(page.getByText('Problems')).toBeVisible();
  14 |   });
  15 | 
  16 |   test('sidebar shows question list', async ({ page }) => {
> 17 |     await page.goto('/');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  18 |     await dismissOnboarding(page);
  19 |     await page.waitForSelector('text=Problems');
  20 |     const sidebar = page.getByRole('complementary').filter({ hasText: 'PROBLEMS' });
  21 |     await expect(sidebar).toBeVisible();
  22 |   });
  23 | 
  24 |   test('settings modal opens and closes', async ({ page }) => {
  25 |     await page.goto('/');
  26 |     await dismissOnboarding(page);
  27 |     await page.getByTitle('Settings').click({ force: true });
  28 |     await expect(page.locator('div').filter({ hasText: 'SETTINGS' }).nth(2)).toBeVisible({ timeout: 5000 });
  29 |     await page.keyboard.press('Escape');
  30 |   });
  31 | 
  32 |   test('sidebar can collapse', async ({ page }) => {
  33 |     await page.goto('/');
  34 |     await dismissOnboarding(page);
  35 |     await page.getByLabel('Collapse sidebar').click({ force: true });
  36 |     await expect(page.getByLabel('Expand sidebar')).toBeVisible();
  37 |   });
  38 | 
  39 |   test('view mode toggle switches to description mode', async ({ page }) => {
  40 |     await page.goto('/');
  41 |     await dismissOnboarding(page);
  42 |     await page.waitForSelector('text=Problems');
  43 |     await page.getByText('Show Active Question').click({ force: true });
  44 |     await expect(page.getByText('Show All Questions')).toBeVisible();
  45 |   });
  46 | });
  47 | 
```