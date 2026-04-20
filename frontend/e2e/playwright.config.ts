/**
 * Playwright E2E Test Configuration
 */
import { defineConfig, devices } from '@playwright/test'

// Environment configuration
const E2E_WEB_PORT = process.env.E2E_WEB_PORT || '4174'
const DEFAULT_BASE_URL = `http://127.0.0.1:${E2E_WEB_PORT}`
const BASE_URL = process.env.E2E_BASE_URL || DEFAULT_BASE_URL
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000'

export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'reports' }],
    ['list'],
  ],

  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: `npm run build && npm run preview -- --host 127.0.0.1 --port ${E2E_WEB_PORT}`,
        url: DEFAULT_BASE_URL,
        timeout: 180000,
        reuseExistingServer: false,
      },

  // Project configuration for different browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chromium',
      },
    },
    {
      name: 'chromium-headed',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chromium',
        headless: false,
      },
    },
  ],
})
