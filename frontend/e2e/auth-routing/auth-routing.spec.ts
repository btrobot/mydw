import { expect, test } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'

test.describe('Auth route gating', () => {
  test('redirects unauthenticated users from protected routes to login', async ({ page }) => {
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

    await page.goto(`${BASE_URL}/#/account`)
    await page.waitForURL('**/#/login')
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })

  test('allows active sessions to mount protected routes', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'authenticated_active',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'active',
          entitlements: ['dashboard:view'],
          expires_at: '2026-04-20T10:00:00',
          last_verified_at: '2026-04-14T00:00:00',
          offline_grace_until: '2026-04-21T10:00:00',
          denial_reason: null,
          device_id: 'device-1',
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/account`)
    await page.waitForURL('**/#/account')
    await expect(page.locator('body')).toContainText('账号管理')
  })

  test('redirects grace sessions away from non-dashboard routes', async ({ page }) => {
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

    await page.goto(`${BASE_URL}/#/account`)
    await page.waitForURL('**/#/auth/grace')
    await expect(page.getByTestId('auth-status-grace')).toBeVisible()
  })

  test('allows grace sessions to mount the restricted dashboard shell', async ({ page }) => {
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

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.locator('body')).toContainText('任务概览')
  })

  test('redirects revoked sessions to revoked shell', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'revoked',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'revoked',
          entitlements: [],
          expires_at: null,
          last_verified_at: '2026-04-14T00:00:00',
          offline_grace_until: null,
          denial_reason: 'revoked',
          device_id: 'device-1',
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/auth/revoked')
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
  })
})
