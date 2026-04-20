import { expect, test } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || ''
const ROOT_URL = BASE_URL || '/'

test.describe('Auth bootstrap', () => {
  test('shows bootstrap loading state before auth session resolves', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1200))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'unauthenticated',
          entitlements: [],
          denial_reason: null,
          device_id: null,
        }),
      })
    })

    await page.goto(ROOT_URL)

    await expect(page.getByTestId('auth-bootstrap-loading')).toBeVisible()
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'ready')
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })

  test('hydrates unauthenticated machine-session state from local backend', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'unauthenticated',
          entitlements: [],
          denial_reason: null,
          device_id: null,
        }),
      })
    })

    await page.goto(ROOT_URL)
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'ready')

    const authState = await page.evaluate(() => document.documentElement.dataset.authState)
    expect(authState).toBe('unauthenticated')
  })

  test('hydrates authenticated_grace machine-session state from local backend', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'authenticated_grace',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'active',
          entitlements: ['dashboard:view'],
          expires_at: null,
          last_verified_at: '2026-04-14T00:00:00',
          offline_grace_until: '2026-04-15T00:00:00',
          denial_reason: 'network_timeout',
          device_id: 'device-1',
        }),
      })
    })

    await page.goto(ROOT_URL)
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'ready')

    const authState = await page.evaluate(() => document.documentElement.dataset.authState)
    expect(authState).toBe('authenticated_grace')
  })

  test('falls back to app shell when auth bootstrap fails', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error_code: 'network_timeout',
            message: 'network timeout',
          },
        }),
      })
    })

    await page.goto(ROOT_URL)
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'error')

    await expect(page.locator('body')).toContainText('Local auth bootstrap failed, but app startup can continue.')
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })
})
