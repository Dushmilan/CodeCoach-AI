import { test, expect } from '@playwright/test';

test.describe('Curriculum Flow', () => {
  test('learn page shows nav link in header', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  });

  test('learn page loads with heading', async ({ page }) => {
    await page.goto('/learn');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Learning Paths')).toBeVisible();
  });

  test('learn page shows courses for unauthenticated user', async ({ page }) => {
    await page.goto('/learn');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Python Fundamentals')).toBeVisible();
    await expect(page.getByText('C Programming')).toBeVisible();
    await expect(page.getByText('Java Fundamentals')).toBeVisible();
  });

  test('course detail shows modules', async ({ page }) => {
    await page.goto('/learn/python-fundamentals');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Getting Started with Python')).toBeVisible();
  });

  test('lesson page loads theory content', async ({ page }) => {
    await page.goto('/learn/lesson/py-hello-world');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Hello, World!')).toBeVisible();
  });

  test('exercise lesson shows editor', async ({ page }) => {
    await page.goto('/learn/lesson/py-io');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('button', { name: /run/i })).toBeVisible();
  });

  test('header has learn link on all pages', async ({ page }) => {
    await page.goto('/learn');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
    await page.goto('/');
    await expect(page.locator('header').getByRole('link', { name: 'Learn' })).toBeVisible();
  });

  test('adjacent navigation arrows visible on lesson', async ({ page }) => {
    await page.goto('/learn/lesson/py-hello-world');
    await page.waitForLoadState('networkidle');
    // First lesson should have a "Next" arrow but no "Previous"
    await expect(page.locator('a[href*="/learn/lesson/py-variables"]')).toBeVisible();
  });

  test('theory lesson shows back to course link', async ({ page }) => {
    await page.goto('/learn/lesson/py-hello-world');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('a[href*="/learn/python-fundamentals"]').first()).toBeVisible();
  });
});
