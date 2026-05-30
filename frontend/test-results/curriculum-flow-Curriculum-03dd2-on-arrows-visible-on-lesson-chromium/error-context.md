# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: curriculum-flow.spec.ts >> Curriculum Flow >> adjacent navigation arrows visible on lesson
- Location: e2e\curriculum-flow.spec.ts:48:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/learn/lesson/py-hello-world
Call log:
  - navigating to "http://localhost:3000/learn/lesson/py-hello-world", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('Curriculum Flow', () => {
  4  |   test('learn page shows nav link in header', async ({ page }) => {
  5  |     await page.goto('/');
  6  |     await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  7  |   });
  8  | 
  9  |   test('learn page loads with heading', async ({ page }) => {
  10 |     await page.goto('/learn');
  11 |     await page.waitForLoadState('networkidle');
  12 |     await expect(page.getByText('Learning Paths')).toBeVisible();
  13 |   });
  14 | 
  15 |   test('learn page shows courses for unauthenticated user', async ({ page }) => {
  16 |     await page.goto('/learn');
  17 |     await page.waitForLoadState('networkidle');
  18 |     await expect(page.getByText('Python Fundamentals')).toBeVisible();
  19 |     await expect(page.getByText('C Programming')).toBeVisible();
  20 |     await expect(page.getByText('Java Fundamentals')).toBeVisible();
  21 |   });
  22 | 
  23 |   test('course detail shows modules', async ({ page }) => {
  24 |     await page.goto('/learn/python-fundamentals');
  25 |     await page.waitForLoadState('networkidle');
  26 |     await expect(page.getByText('Getting Started with Python')).toBeVisible();
  27 |   });
  28 | 
  29 |   test('lesson page loads theory content', async ({ page }) => {
  30 |     await page.goto('/learn/lesson/py-hello-world');
  31 |     await page.waitForLoadState('networkidle');
  32 |     await expect(page.getByText('Hello, World!')).toBeVisible();
  33 |   });
  34 | 
  35 |   test('exercise lesson shows editor', async ({ page }) => {
  36 |     await page.goto('/learn/lesson/py-io');
  37 |     await page.waitForLoadState('networkidle');
  38 |     await expect(page.getByRole('button', { name: /run/i })).toBeVisible();
  39 |   });
  40 | 
  41 |   test('header has learn link on all pages', async ({ page }) => {
  42 |     await page.goto('/learn');
  43 |     await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  44 |     await page.goto('/');
  45 |     await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  46 |   });
  47 | 
  48 |   test('adjacent navigation arrows visible on lesson', async ({ page }) => {
> 49 |     await page.goto('/learn/lesson/py-hello-world');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/learn/lesson/py-hello-world
  50 |     await page.waitForLoadState('networkidle');
  51 |     // First lesson should have a "Next" arrow but no "Previous"
  52 |     await expect(page.locator('a[href*="/learn/lesson/py-variables"]')).toBeVisible();
  53 |   });
  54 | 
  55 |   test('theory lesson shows back to course link', async ({ page }) => {
  56 |     await page.goto('/learn/lesson/py-hello-world');
  57 |     await page.waitForLoadState('networkidle');
  58 |     await expect(page.locator('a[href*="/learn/python-fundamentals"]').first()).toBeVisible();
  59 |   });
  60 | });
  61 | 
```