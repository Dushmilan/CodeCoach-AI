import { test, expect, type Page } from '@playwright/test';

// Admin hierarchy tree on the admin dashboard (Issue #159, Task 6).
// Seeds: backend/scripts/seed_admin.py (admin/admin123) +
// backend/scripts/seed_classroom_demo.py (professors, CS101/CS201 rooms,
// demonstrator.turing as TA) against the isolated test schema.

async function loginAsAdmin(page: Page) {
  await page.goto('/admin/login');
  await page.waitForLoadState('domcontentloaded');
  await page.getByLabel(/username/i).fill('admin');
  await page.getByLabel(/password/i).fill('admin123');
  await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
  await page.waitForURL('**/admin/dashboard', { timeout: 15000 });
}

test.describe('Admin hierarchy', () => {
  test('dashboard lists each professor with courses and classroom analytics', async ({
    page,
  }) => {
    await loginAsAdmin(page);
    const section = page.getByTestId('hierarchy-section');
    await expect(section).toBeVisible({ timeout: 15000 });
    await expect(section.getByText('professor.ada')).toBeVisible();
    await expect(section.getByText('professor.grace')).toBeVisible();
    await expect(section.getByText('CS101 · Section A')).toBeVisible();
    await expect(section.getByText('CS101-A-2026')).toBeVisible();
    await expect(section.getByText('demonstrator.turing').first()).toBeVisible();
    await expect(section.getByText(/5 students/).first()).toBeVisible();
    await expect(section.getByText(/avg completion/).first()).toBeVisible();
  });
});
