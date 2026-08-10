import { test, expect, Page, Route } from '@playwright/test';

const SENIOR_QUESTIONS = [
  'Why a hashmap?',
  'What about space complexity?',
  'What edge cases did you consider?',
];

const REPORT_BODY = {
  summary: 'You explained your approach clearly.',
  exchanges: [
    {
      question: 'Why a hashmap?',
      answer: 'For O(1) lookups.',
      strengths: ['Identified the right data structure'],
      improvements: ['Mention the memory tradeoff'],
      stronger_answer_should_include: ['Space complexity'],
    },
    {
      question: 'What about space complexity?',
      answer: "I'm not sure.",
      strengths: [],
      improvements: ['Space is O(n) because the hashmap stores every key'],
      stronger_answer_should_include: ['Talk through the tradeoff'],
    },
    {
      question: 'What edge cases did you consider?',
      answer: 'I did not think about edge cases.',
      strengths: [],
      improvements: ['Duplicates would silently overwrite the first entry'],
      stronger_answer_should_include: ['Duplicate values and empty input'],
    },
  ],
  takeaway: 'Teaching your code is the fastest way to find gaps.',
};

function stubSubmitPass(route: Route) {
  void route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      passed: true,
      total: 1,
      passed_count: 1,
      results: [
        {
          index: 1,
          passed: true,
          hidden: true,
          input: '',
          expected: '',
          actual: '',
        },
      ],
    }),
  });
}

function stubCoaching(page: Page, opts?: { reportStatus?: number }) {
  let questionIndex = 0;
  return page.route('**/api/coach/**', (route) => {
    const url = route.request().url();
    if (url.includes('/debrief-report')) {
      const status = opts?.reportStatus ?? 200;
      void route.fulfill({
        status,
        contentType: 'application/json',
        body:
          status === 200
            ? JSON.stringify(REPORT_BODY)
            : JSON.stringify({ detail: 'Internal Server Error' }),
      });
      return;
    }
    const question = SENIOR_QUESTIONS[questionIndex % SENIOR_QUESTIONS.length];
    questionIndex += 1;
    void route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ response: question, structured: null }),
    });
  });
}

async function openDebriefFlow(page: Page) {
  const ts = Date.now();
  await page.goto('/register');
  await page.waitForLoadState('domcontentloaded');
  await page.getByLabel(/username/i).fill('debrief' + ts);
  await page.getByLabel(/email/i).fill('debrief' + ts + '@test.com');
  await page.getByLabel(/password/i).fill('DebriefPass123!');
  await page.getByRole('button', { name: /create account|register/i }).click();
  await expect(page).toHaveURL('/');

  await page.evaluate(() => localStorage.setItem('onboarding-done', 'true'));
  await page.goto('/problems');
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('table tbody tr');
  await page.locator('table tbody tr').first().click();
  await page.waitForLoadState('networkidle');
  await page.waitForSelector('.monaco-editor', { timeout: 15000 });

  await page.getByRole('button', { name: /submit/i }).click();
  await expect(page.getByText(/mission complete/i)).toBeVisible({ timeout: 15000 });
}

async function runFullDebrief(page: Page) {
  await page.getByRole('button', { name: /start debrief/i }).click();
  await expect(page.getByText(/Milo, Junior Dev/i)).toBeVisible({ timeout: 15000 });

  for (const question of SENIOR_QUESTIONS) {
    await expect(page.getByText(new RegExp(question))).toBeVisible({
      timeout: 15000,
    });
    await page
      .getByPlaceholder(/explain your approach to milo/i)
      .fill(`Answer to: ${question}`);
    await page.getByRole('button', { name: /submit explanation/i }).click();
  }

  await expect(
    page.getByRole('button', { name: /view debrief report/i }),
  ).toBeVisible({ timeout: 15000 });
  await page.getByRole('button', { name: /view debrief report/i }).click();
}

test.describe('Reverse Interview Debrief Flow', () => {
  test('solves a problem, completes the 3-round debrief and sees the report', async ({
    page,
  }) => {
    await stubCoaching(page);
    await page.route('**/api/submit/', stubSubmitPass);

    await openDebriefFlow(page);
    await runFullDebrief(page);

    await expect(page.getByText('Mission Debrief')).toBeVisible({
      timeout: 15000,
    });
    await expect(
      page.getByText(/you explained your approach clearly/i),
    ).toBeVisible();
    await expect(page.getByText('Why a hashmap?', { exact: true })).toBeVisible();
    await expect(page.getByText(/O\(1\) lookups/)).toBeVisible();
    await expect(page.getByText('Identified the right data structure')).toBeVisible();
    await expect(page.getByText('Space complexity', { exact: true })).toBeVisible();
    await expect(page.getByText("Milo's Feedback").first()).toBeVisible();
    await expect(page.getByText(/I'm not sure/)).toBeVisible();
    await expect(
      page.getByText('Duplicates would silently overwrite the first entry'),
    ).toBeVisible();
    await expect(page.getByText(/teaching your code/i)).toBeVisible();

    await page.getByRole('button', { name: /continue learning/i }).click();
    await expect(page.getByText(/mission complete/i)).not.toBeVisible();
  });

  test('skipping the debrief closes the overlay without a report', async ({
    page,
  }) => {
    await stubCoaching(page);
    await page.route('**/api/submit/', stubSubmitPass);

    await openDebriefFlow(page);
    await page.getByRole('button', { name: /skip debrief/i }).click();

    await expect(page.getByText(/mission complete/i)).not.toBeVisible();
    await expect(
      page.getByRole('button', { name: /start debrief/i }),
    ).not.toBeVisible();
  });

  test('shows a fallback report with captured Q&A when the report API fails', async ({
    page,
  }) => {
    await stubCoaching(page, { reportStatus: 500 });
    await page.route('**/api/submit/', stubSubmitPass);

    await openDebriefFlow(page);
    await runFullDebrief(page);

    await expect(page.getByText('Mission Debrief')).toBeVisible({
      timeout: 15000,
    });
    await expect(
      page.getByText('Why a hashmap?', { exact: true }),
    ).toBeVisible();
    await expect(page.getByText(/Answer to: Why a hashmap/)).toBeVisible();
    await expect(page.getByText(/teaching your code/i)).toBeVisible();
    await expect(
      page.getByRole('button', { name: /continue learning/i }),
    ).toBeEnabled();
  });
});
