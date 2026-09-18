import { test, expect, type Page } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

// Browser-automatable edge cases across auth, problems, execution,
// curriculum, and settings. All accounts come from backend seed scripts
// (seed_admin.py + seed_classroom_demo.py); only the round-trip test
// creates a user, with a timestamp-unique name.

// Covers: wrong/unknown credentials, duplicate registration, logout,
// session persistence, cross-role guards, empty search, unknown ids,
// markup-neutral search, Piston syntax-error output, editor reset,
// error boundary, theme toggle, privacy page.

async function login(page: Page, username: string, password: string, path = '/login') {
  await page.goto(path);
  await page.waitForLoadState('domcontentloaded');
  await page.getByLabel(/username/i).fill(username);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
}

async function logout(page: Page) {
  await page.locator('header').getByRole('button', { name: /settings/i }).click();
  await page.getByTestId('settings-tab-account').click();
  await page.getByRole('button', { name: /sign out|log out/i }).click();
}

test.describe('Auth edge cases', () => {
  test('wrong password shows 401 and stays on login', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill('mia');
    await page.getByLabel(/password/i).fill('wrongpass123');
    await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
    await expect(page.getByText(/request failed: 401/i)).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL('/login');
  });

  test('unknown username shows 401 and stays on login', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill('nosuchuser');
    await page.getByLabel(/password/i).fill('whatever123');
    await page.getByRole('main').getByRole('button', { name: /sign in/i }).click();
    await expect(page.getByText(/request failed: 401/i)).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL('/login');
  });

  test('duplicate username registration shows 409 conflict', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill('admin');
    await page.getByLabel(/email/i).fill('dup@test.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /create account|register/i }).click();
    await expect(page.getByText(/request failed: 409/i)).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL('/register');
  });

  test('logout via settings returns to sign-in', async ({ page }) => {
    await login(page, 'mia', 'student123');
    await expect(page).toHaveURL('/', { timeout: 20000 });
    await dismissOnboarding(page);
    await logout(page);
    await page.waitForURL('**/login', { timeout: 15000 });
    await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible();
  });

  test('session persists across reload', async ({ page }) => {
    await login(page, 'mia', 'student123');
    await expect(page).toHaveURL('/', { timeout: 20000 });
    await page.reload();
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('header').getByText('mia')).toBeVisible({ timeout: 15000 });
  });

  test('fresh account round-trips register, logout, login', async ({ page }) => {
    const ts = Date.now();
    const username = 'edgeuser' + ts;
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel(/username/i).fill(username);
    await page.getByLabel(/email/i).fill('edge' + ts + '@test.com');
    await page.getByLabel(/password/i).fill('TestPass123!');
    await page.getByRole('button', { name: /create account|register/i }).click();
    await expect(page).toHaveURL('/', { timeout: 15000 });
    await dismissOnboarding(page);
    await logout(page);
    await page.waitForURL('**/login', { timeout: 15000 });
    await login(page, username, 'TestPass123!');
    await expect(page).toHaveURL('/', { timeout: 20000 });
  });

  test('student sees Access Denied on admin dashboard', async ({ page }) => {
    await login(page, 'mia', 'student123');
    await expect(page).toHaveURL('/', { timeout: 20000 });
    await page.goto('/admin/dashboard');
    await expect(page.getByText('Access Denied')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/admin privileges/i)).toBeVisible();
    await page.getByRole('link', { name: /go home/i }).click();
    await expect(page).toHaveURL('/', { timeout: 15000 });
  });

  test('TA sees Access Denied on professor dashboard', async ({ page }) => {
    await login(page, 'demonstrator.turing', 'demonstrator123');
    await expect(page).toHaveURL('/demonstrator', { timeout: 20000 });
    await page.goto('/professor');
    await expect(page.getByText('Access Denied')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/professor privileges/i)).toBeVisible();
  });

  test('professor can view demonstrator dashboard', async ({ page }) => {
    await login(page, 'professor.ada', 'professor123');
    await expect(page).toHaveURL('/professor', { timeout: 20000 });
    await page.goto('/demonstrator');
    await expect(page.getByRole('heading', { name: /demonstrator dashboard/i })).toBeVisible({
      timeout: 15000,
    });
  });

  test('unauthenticated professor area redirects to sign-in', async ({ page }) => {
    await page.goto('/professor');
    await page.waitForURL('**/login', { timeout: 15000 });
    await expect(page.getByRole('main').getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('unauthenticated demonstrator area redirects to sign-in', async ({ page }) => {
    await page.goto('/demonstrator');
    await page.waitForURL('**/login', { timeout: 15000 });
    await expect(page.getByRole('main').getByRole('button', { name: /sign in/i })).toBeVisible();
  });
});

test.describe('Problems edge cases', () => {
  test('gibberish search shows empty result count', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.getByPlaceholder(/search by title/i).fill('zzz-no-such-problem');
    await expect(page.getByText(/no questions match your filters/i)).toBeVisible({ timeout: 15000 });
    await page.getByRole('button', { name: /clear all filters/i }).click();
    await expect(page.getByText(/showing \d+ of \d+ questions/i)).toBeVisible({ timeout: 15000 });
  });

  test('unknown problem id shows 404 with working back link', async ({ page }) => {
    await page.goto('/problems/no-such-problem-xyz');
    await expect(page.getByText(/404/i)).toBeVisible({ timeout: 15000 });
    await page.getByRole('link', { name: /back to problems/i }).click();
    await page.waitForURL('**/problems', { timeout: 15000 });
    await expect(page.getByRole('heading', { name: 'Problems' })).toBeVisible();
  });

  test('search input neutralizes markup', async ({ page }) => {
    await page.goto('/problems');
    await dismissOnboarding(page);
    await page.waitForSelector('tbody tr', { timeout: 15000 });
    await page.getByPlaceholder(/search by title/i).fill('<img src=x onerror=alert(1)>');
    await expect(page.getByText(/no questions match your filters/i)).toBeVisible({ timeout: 15000 });
    await expect(page.locator('table img')).toHaveCount(0);
  });
});

test.describe('Execution edge cases', () => {
  async function openTwoSum(page: Page) {
    // Run/Reset/Submit require sign-in (disabled={isRunning || !isAuthenticated})
    await login(page, 'mia', 'student123');
    await expect(page).toHaveURL('/', { timeout: 20000 });
    await page.goto('/problems/two-sum');
    await expect(page.getByRole('heading', { name: /two sum/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: /^run$/i })).toBeEnabled({ timeout: 20000 });
    await page.locator('.monaco-editor').click();
  }

  test('run with syntax error surfaces error output', async ({ page }) => {
    await openTwoSum(page);
    await page.keyboard.press('ControlOrMeta+a');
    await page.keyboard.type('def broken(:\n  pass');
    await expect(page.locator('.monaco-editor .view-lines')).toContainText('broken', {
      timeout: 15000,
    });
    await page.getByRole('button', { name: /^run$/i }).click();
    // Broken code surfaces as structured test results, not raw stderr
    await expect(page.getByText(/test results/i)).toBeVisible({ timeout: 60000 });
    await expect(page.getByText(/0\/1 passed/i)).toBeVisible();
  });

  test('reset restores starter code', async ({ page }) => {
    await openTwoSum(page);
    await page.keyboard.press('ControlOrMeta+a');
    await page.keyboard.type('print("garbage")');
    await page.getByRole('button', { name: /reset/i }).click();
    await expect(page.locator('.monaco-editor .view-lines')).toContainText('def two_sum', {
      timeout: 15000,
    });
  });
});

test.describe('Curriculum and settings edge cases', () => {
  test('unknown lesson shows error boundary', async ({ page }) => {
    await page.goto('/learn/lesson/no-such-lesson-xyz');
    await expect(page.locator('body')).toContainText(/error/i, { timeout: 15000 });
  });

  test('real course page shows its content', async ({ page }) => {
    await page.goto('/learn/python-fundamentals');
    await expect(page.getByRole('heading', { name: /python fundamentals/i })).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByText(/created by/i)).toBeVisible();
  });

  test('privacy page renders policy', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page.getByRole('heading', { name: /privacy policy/i })).toBeVisible({
      timeout: 15000,
    });
  });

  test('theme toggle switches color scheme', async ({ page }) => {
    await page.goto('/');
    await dismissOnboarding(page);
    const html = page.locator('html');
    await expect(html).toHaveClass(/dark/, { timeout: 15000 });
    await page.getByRole('button', { name: 'Toggle theme' }).click();
    await expect(html).toHaveClass(/light/, { timeout: 15000 });
    await page.getByRole('button', { name: 'Toggle theme' }).click();
    await expect(html).toHaveClass(/dark/, { timeout: 15000 });
  });
});
