import { defineConfig, devices } from '@playwright/test';

// Minimal runner for the viewer duration harness (issue #155).
// Boots the lab's own vite dev server so `/viewer.html?token=…` resolves
// against the real scene + Player wiring.
export default defineConfig({
  testDir: './tests',
  // 18-beat payloads need ~45s+ of wall-clock playback; keep the default
  // test timeout above the longest per-assertion timeout in the suite.
  timeout: 90_000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:9000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  expect: { timeout: 10000 },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'pnpm dev --port 9000 --strictPort',
    url: 'http://localhost:9000/viewer.html',
    reuseExistingServer: true,
    timeout: 180000,
  },
});
