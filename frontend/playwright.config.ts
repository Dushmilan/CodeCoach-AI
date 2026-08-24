import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { outputFolder: 'e2e-report' }], ['list']],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'] } },
  ],
  webServer: [
    {
      command: 'pnpm dev',
      port: 3000,
      reuseExistingServer: true,
      timeout: 120000,
      // Same-origin API base: keeps browser calls under CSP connect-src
      // 'self' (the /api rewrite proxies to the backend). Without this a
      // developer .env pointing at http://localhost:8000 gets blocked.
      env: { NEXT_PUBLIC_API_URL: '' },
    },
    {
      command: 'pnpm --dir ../motion-canvas-lab dev --port 9000 --strictPort',
      url: 'http://localhost:9000/viewer.html',
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
});
