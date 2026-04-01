/**
 * Playwright E2E Test Configuration
 *
 * Configuration for E2E testing using Playwright with Patchright's browser engine
 * for anti-detection capabilities (same as backend automation).
 */

import { defineConfig, devices } from '@playwright/test'
import path from 'path'

// Environment configuration
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'e2e/reports' }],
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

  // Global setup and teardown
  globalSetup: path.join(__dirname, 'e2e/setup.ts'),
  globalTeardown: path.join(__dirname, 'e2e/teardown.ts'),

  // Project configuration for different browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Use Patchright's chromium for anti-detection (same as backend automation)
        channel: 'chromium',
        launchOptions: {
          args: [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
          ],
        },
      },
    },
    {
      name: 'chromium-headed',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chromium',
        launchOptions: {
          args: [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
          ],
        },
        headless: false,
      },
    },
    // Patchright browser (same as backend automation)
    {
      name: 'patchright-chromium',
      use: {
        browserName: 'chromium',
        launchOptions: {
          // Patchright handles anti-detection automatically
          args: [
            '--disable-dev-shm-usage',
            '--no-sandbox',
          ],
        },
      },
      testMatch: /.*\.spec\.ts/,
    },
  ],

  // Web server configuration for local development
  webServer: [
    {
      command: 'npm run dev',
      url: BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: 'cd ../backend && python -m uvicorn main:app --reload --port 8000',
      url: API_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
      cwd: path.resolve(__dirname, '..'),
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
})
