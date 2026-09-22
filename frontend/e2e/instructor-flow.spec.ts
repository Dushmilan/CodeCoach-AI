import { test, expect, type Page } from '@playwright/test';

// Role-based post-login routing + header gating for professor/demonstrator
// dashboards (Issue #159). Uses seeded instructor credentials from
// backend/scripts/seed_admin.py against the isolated test schema.

async function login(page: Page, username: string, password: string) {
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');
  await page.getByLabel(/username/i).fill(username);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
}

test.describe('Instructor role flow', () => {
  test('professor lands on professor dashboard with only the professor link', async ({ page }) => {
    await login(page, 'professor.ada', 'professor123');
    await expect(page).toHaveURL('/professor', { timeout: 15000 });
    await expect(page.getByRole('heading', { name: 'Professor Dashboard' })).toBeVisible();
    await expect(page.getByTestId('header-professor-link')).toBeVisible();
    await expect(page.getByTestId('header-demonstrator-link')).toHaveCount(0);
  });

  test('ta lands on demonstrator dashboard with only the demonstrator link', async ({ page }) => {
    await login(page, 'demonstrator.turing', 'demonstrator123');
    await expect(page).toHaveURL('/demonstrator', { timeout: 15000 });
    await expect(page.getByTestId('header-demonstrator-link')).toBeVisible();
    await expect(page.getByTestId('header-professor-link')).toHaveCount(0);
  });

  test('professor classroom list and detail render roster and risk stats', async ({ page }) => {
    await login(page, 'professor.ada', 'professor123');
    await expect(page).toHaveURL('/professor', { timeout: 15000 });
    await page.goto('/professor/classrooms');
    await expect(page.getByText('CS101 · Section A')).toBeVisible();
    await page.getByRole('link', { name: 'Open classroom' }).first().click();
    await expect(page.getByText('Roster and enrollment')).toBeVisible();
    await expect(page.getByTestId('roster-table')).toBeVisible();
    await expect(page.getByText('At risk')).toBeVisible();
  });

  test('professor analytics page renders class aggregates', async ({ page }) => {
    await login(page, 'professor.ada', 'professor123');
    await expect(page).toHaveURL('/professor', { timeout: 15000 });
    await page.goto('/professor/analytics');
    await expect(page.getByRole('heading', { name: 'Class Analytics' })).toBeVisible();
  });
});
