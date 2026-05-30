# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth-flow.spec.ts >> Auth Flow >> register navigates to home after success
- Location: e2e\auth-flow.spec.ts:30:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/register
Call log:
  - navigating to "http://localhost:3000/register", waiting until "load"

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
  8  | test.describe('Auth Flow', () => {
  9  |   test('shows sign in button when logged out', async ({ page }) => {
  10 |     await page.goto('/');
  11 |     await dismissOnboarding(page);
  12 |     await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible();
  13 |   });
  14 | 
  15 |   test('login page has required fields', async ({ page }) => {
  16 |     await page.goto('/login');
  17 |     await expect(page.getByLabel(/username/i)).toBeVisible();
  18 |     await expect(page.getByLabel(/password/i)).toBeVisible();
  19 |     await expect(page.getByRole('button', { name: 'Sign in', exact: true })).toBeVisible();
  20 |   });
  21 | 
  22 |   test('register page has all fields', async ({ page }) => {
  23 |     await page.goto('/register');
  24 |     await expect(page.getByLabel(/username/i)).toBeVisible();
  25 |     await expect(page.getByLabel(/email/i)).toBeVisible();
  26 |     await expect(page.getByLabel(/password/i)).toBeVisible();
  27 |     await expect(page.getByRole('button', { name: /create account|register/i })).toBeVisible();
  28 |   });
  29 | 
  30 |   test('register navigates to home after success', async ({ page }) => {
> 31 |     await page.goto('/register');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/register
  32 |     const ts = Date.now();
  33 |     await page.getByLabel(/username/i).fill('e2euser' + ts);
  34 |     await page.getByLabel(/email/i).fill('e2e' + ts + '@test.com');
  35 |     await page.getByLabel(/password/i).fill('TestPass123!');
  36 |     await page.getByRole('button', { name: /create account|register/i }).click();
  37 |     await expect(page).toHaveURL('/');
  38 |   });
  39 | 
  40 |   test('learn page shows curriculum when logged out', async ({ page }) => {
  41 |     await page.goto('/learn');
  42 |     await page.waitForLoadState('networkidle');
  43 |     await expect(page.locator('body')).toBeVisible();
  44 |   });
  45 | });
  46 | 
```