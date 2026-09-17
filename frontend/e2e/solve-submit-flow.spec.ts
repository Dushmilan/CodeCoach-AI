import { test, expect, Page } from '@playwright/test';
import { dismissOnboarding } from './helpers/auth';

const SOLUTION = [
  'def two_sum(nums, target):',
  '    seen = {}',
  '    for i, n in enumerate(nums):',
  '        if target - n in seen:',
  '            return [seen[target - n], i]',
  '        seen[n] = i',
].join('\n');

async function registerFreshUser(page: Page, tag: string) {
  const ts = Date.now();
  await page.goto('/register');
  await page.getByLabel(/username/i).fill(`${tag}${ts}`);
  await page.getByLabel(/email/i).fill(`${tag}${ts}@test.com`);
  await page.getByLabel(/password/i).fill('TestPass123!');
  await page.getByRole('button', { name: /create account|register/i }).click();
  await expect(page).toHaveURL('/', { timeout: 15000 });
}

async function openTwoSumWithSolution(page: Page) {
  await page.goto('/problems/two-sum');
  await dismissOnboarding(page);
  await expect(page.locator('.monaco-editor')).toBeVisible({ timeout: 15000 });
  // Paste (not keystroke injection): Monaco's auto-closing pairs scramble
  // fast typed brackets, producing genuinely broken code.
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.evaluate(
    (text) => navigator.clipboard.writeText(text),
    SOLUTION,
  );
  await page.locator('.monaco-editor').click();
  await page.keyboard.press('ControlOrMeta+a');
  await page.keyboard.press('ControlOrMeta+v');
  await expect(page.locator('.monaco-editor .view-lines')).toContainText(
    'enumerate',
    { timeout: 15000 },
  );
}

test.describe('Solve and submit loop', () => {
  test('run passes then submit grades and persists progress', async ({
    page,
  }) => {
    test.setTimeout(180000);
    await registerFreshUser(page, 'solver');
    await openTwoSumWithSolution(page);

    await page.getByRole('button', { name: /^run$/i }).click();
    await expect(page.getByText(/Test Results: 1\/1 passed/)).toBeVisible({
      timeout: 90000,
    });

    await page.getByRole('button', { name: /submit/i }).click();
    // Submit re-renders the same results banner (the raw "Submit Results:"
    // string only surfaces for interactive questions); the success toast
    // fires solely when passed_count === total, so it proves grading.
    await expect(page.getByText('All tests passed!')).toBeVisible({
      timeout: 20000,
    });

    const progress = await page.evaluate(() =>
      localStorage.getItem('user_progress'),
    );
    expect(progress).toContain('"two-sum":"solved"');
  });

  test('double submit in flight sends a single request', async ({ page }) => {
    test.setTimeout(180000);
    await registerFreshUser(page, 'dblclick');
    await openTwoSumWithSolution(page);

    let submitCalls = 0;
    await page.route('**/api/submit/', async (route) => {
      submitCalls += 1;
      await new Promise((r) => setTimeout(r, 1500));
      await route.continue();
    });

    await page.getByRole('button', { name: /submit/i }).dblclick();
    await expect(page.getByText('All tests passed!')).toBeVisible({
      timeout: 20000,
    });
    expect(submitCalls).toBe(1);
  });
});
