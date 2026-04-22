import { expect, test } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || ''

test.describe('Auth status live-state feedback', () => {
  test('shows an explicit live error when shell status refresh fails', async ({ page }) => {
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

    await page.route('**/api/auth/status', async (route) => {
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

    await page.goto(`${BASE_URL}/#/auth/revoked`, { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('auth-status-primary-alert')).toBeVisible()
    await expect(page.getByTestId('auth-status-live-error')).toBeVisible()
    await expect(page.getByTestId('auth-status-live-error')).toContainText('暂时无法刷新')
  })
})
