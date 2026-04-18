import { expect, test } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'
const BOOTSTRAP_WARNING = 'Local auth bootstrap failed, but app startup can continue.'

const createSession = (overrides: Record<string, unknown> = {}) => ({
  auth_state: 'unauthenticated',
  entitlements: [],
  denial_reason: null,
  device_id: null,
  ...overrides,
})

const createStatus = (overrides: Record<string, unknown> = {}) => ({
  auth_state: 'unauthenticated',
  remote_user_id: null,
  display_name: null,
  license_status: null,
  device_id: null,
  denial_reason: null,
  expires_at: null,
  last_verified_at: null,
  offline_grace_until: null,
  token_expires_in_seconds: null,
  grace_remaining_seconds: null,
  is_authenticated: false,
  is_active: false,
  is_grace: false,
  requires_reauth: false,
  can_read_local_data: false,
  can_run_protected_actions: false,
  can_run_background_tasks: false,
  ...overrides,
})

test.describe('Auth error UX', () => {
  test('shows a friendly login error for invalid credentials', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSession()),
      })
    })

    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error_code: 'invalid_credentials',
            message: 'Invalid username or password',
          },
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/login`)
    await page.locator('input#username').fill('alice')
    await page.locator('input#password').fill('wrong-password')
    await page.locator('button[type="submit"]').click()

    await expect(page.getByTestId('auth-login-error-message')).toBeVisible()
    await expect(page.getByTestId('auth-login-error-message').locator('button')).toBeVisible()
  })

  test('shows an offline-friendly message when auth bootstrap fails', async ({ page }) => {
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

    await page.goto(BASE_URL)
    await expect(page.getByTestId('auth-bootstrap-error')).toBeVisible()
    await expect(page.locator('body')).toContainText(BOOTSTRAP_WARNING)
    await expect(page.getByTestId('auth-bootstrap-error').locator('button')).toBeVisible()
  })

  test('shows a re-login prompt on the revoked auth shell', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSession({ auth_state: 'revoked', display_name: 'Alice', device_id: 'device-1' })),
      })
    })

    await page.route('**/api/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createStatus({
          auth_state: 'revoked',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'revoked',
          device_id: 'device-1',
          denial_reason: 'revoked',
          last_verified_at: '2026-04-14T00:00:00',
          requires_reauth: true,
        })),
      })
    })

    await page.goto(`${BASE_URL}/#/auth/revoked`)
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
    await expect(page.getByTestId('auth-status-live-revoked')).toBeVisible()
    await expect(page.getByTestId('auth-status-session-meta')).toContainText('Alice')
    await expect(page.getByTestId('auth-status-signout-button')).toBeVisible()
  })
})
