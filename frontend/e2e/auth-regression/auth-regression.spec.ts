import { expect, test } from '@playwright/test'

import { mockWorkbenchLandingApis } from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'
const BOOTSTRAP_WARNING = 'Local auth bootstrap failed, but app startup can continue.'

test.describe('Auth regression and polish', () => {
  test('redirects authenticated users away from login and shows auth session header', async ({ page }) => {
    await mockWorkbenchLandingApis(page)

    await page.goto(`${BASE_URL}/#/login`)
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('auth-session-header')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    await expect(page.locator('body')).toContainText('Alice')
    await expect(page.locator('body')).toContainText('Authenticated')
  })

  test('signs out from header and returns to login', async ({ page }) => {
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

    await page.route('**/api/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'unauthenticated',
          remote_user_id: null,
          display_name: null,
          license_status: null,
          entitlements: [],
          expires_at: null,
          last_verified_at: null,
          offline_grace_until: null,
          denial_reason: null,
          device_id: null,
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/dashboard`)
    await expect(page.getByTestId('auth-session-header')).toBeVisible()
    await page.getByTestId('auth-logout-button').click()
    await page.waitForURL('**/#/login')
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })

  test('signs out from a locked auth status page and returns to login', async ({ page }) => {
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

    await page.route('**/api/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'unauthenticated',
          remote_user_id: null,
          display_name: null,
          license_status: null,
          entitlements: [],
          expires_at: null,
          last_verified_at: null,
          offline_grace_until: null,
          denial_reason: null,
          device_id: null,
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/auth/revoked`)
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
    await page.getByTestId('auth-status-signout-button').click()
    await page.waitForURL('**/#/login')
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })

  test('shows retry affordance when bootstrap fails', async ({ page }) => {
    let callCount = 0
    await page.route('**/api/auth/session', async (route) => {
      callCount += 1
      if (callCount === 1) {
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
        return
      }

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

    await page.goto(BASE_URL)
    await expect(page.locator('body')).toContainText(BOOTSTRAP_WARNING)
    await page.getByRole('button', { name: 'Retry' }).click()
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'ready')
  })
})
