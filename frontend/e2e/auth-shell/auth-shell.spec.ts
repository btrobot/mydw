import { expect, test, type Page } from '@playwright/test'

import { createAuthSession, mockWorkbenchLandingApis } from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'

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

async function mockStatusShell(page: Page, variant: 'revoked' | 'device_mismatch' | 'expired' | 'grace') {
  const authState = variant === 'device_mismatch' ? 'device_mismatch' : variant
  await page.route('**/api/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createAuthSession(variant === 'grace' ? 'authenticated_grace' : variant === 'revoked' ? 'revoked' : 'unauthenticated', {
        display_name: 'Alice',
        device_id: 'device-1',
      })),
    })
  })

  await page.route('**/api/auth/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createStatus({
        auth_state: authState,
        display_name: 'Alice',
        device_id: 'device-1',
        denial_reason: variant === 'grace' ? 'network_timeout' : variant,
        requires_reauth: variant !== 'grace',
        is_authenticated: variant === 'grace',
        is_grace: variant === 'grace',
        can_read_local_data: variant === 'grace',
      })),
    })
  })
}

test.describe('Auth shell pages', () => {
  test('renders login page and submits successful login to local auth surface', async ({ page }) => {
    await mockWorkbenchLandingApis(page, { authState: 'unauthenticated' })

    await page.route('**/api/auth/login', async (route) => {
      const body = await route.request().postDataJSON()
      expect(body.username).toBe('alice')
      expect(body.password).toBe('secret')
      expect(body.device_id).toBeTruthy()

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
          device_id: body.device_id,
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/login`)
    await expect(page.getByTestId('auth-login-page')).toBeVisible()

    await page.locator('input#username').fill('alice')
    await page.locator('input#password').fill('secret')
    await page.locator('button[type="submit"]').click()

    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
  })

  test('renders revoked shell', async ({ page }) => {
    await mockStatusShell(page, 'revoked')
    await page.goto(`${BASE_URL}/#/auth/revoked`)
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
    await expect(page.getByTestId('auth-status-signout-button')).toBeVisible()
  })

  test('renders device mismatch shell', async ({ page }) => {
    await mockStatusShell(page, 'device_mismatch')
    await page.goto(`${BASE_URL}/#/auth/device-mismatch`)
    await expect(page.getByTestId('auth-status-device_mismatch')).toBeVisible()
    await expect(page.getByTestId('auth-status-signout-button')).toBeVisible()
  })

  test('renders expired shell', async ({ page }) => {
    await mockStatusShell(page, 'expired')
    await page.goto(`${BASE_URL}/#/auth/expired`)
    await expect(page.getByTestId('auth-status-expired')).toBeVisible()
    await expect(page.getByTestId('auth-status-signout-button')).toBeVisible()
  })

  test('renders grace shell', async ({ page }) => {
    await mockStatusShell(page, 'grace')
    await page.goto(`${BASE_URL}/#/auth/grace`)
    await expect(page.getByTestId('auth-status-grace')).toBeVisible()
    await expect(page.getByTestId('auth-status-signout-button')).toBeVisible()
  })
})
