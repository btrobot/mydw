import { expect, test, type Page } from '@playwright/test'

import {
  createAuthSession,
  mockDashboardRuntimeApis,
  mockWorkbenchLandingApis,
} from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || ''

const createLockedSession = (authState: 'revoked' | 'device_mismatch' | 'expired') => ({
  auth_state: authState,
  remote_user_id: 'u_123',
  display_name: 'Alice',
  license_status: authState === 'revoked' ? 'revoked' : 'active',
  entitlements: [],
  expires_at: null,
  last_verified_at: '2026-04-14T00:00:00',
  offline_grace_until: null,
  denial_reason: authState,
  device_id: 'device-1',
})

const createStatus = (authState: 'revoked' | 'device_mismatch' | 'expired') => ({
  auth_state: authState,
  remote_user_id: 'u_123',
  display_name: 'Alice',
  license_status: authState === 'revoked' ? 'revoked' : 'active',
  device_id: 'device-1',
  denial_reason: authState,
  expires_at: null,
  last_verified_at: '2026-04-14T00:00:00',
  offline_grace_until: null,
  token_expires_in_seconds: null,
  grace_remaining_seconds: null,
  is_authenticated: false,
  is_active: false,
  is_grace: false,
  requires_reauth: true,
  can_read_local_data: false,
  can_run_protected_actions: false,
  can_run_background_tasks: false,
})

async function mockProtectedShellApis(page: Page, authState: 'authenticated_active' | 'authenticated_grace') {
  await mockWorkbenchLandingApis(page, { authState })
  await mockDashboardRuntimeApis(page)

  await page.route('**/api/accounts**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    })
  })
}

async function mockLockedShellApis(page: Page, authState: 'revoked' | 'device_mismatch' | 'expired') {
  await page.route('**/api/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createLockedSession(authState)),
    })
  })

  await page.route('**/api/auth/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createStatus(authState)),
    })
  })
}

test.describe('Auth route gating', () => {
  test('redirects unauthenticated users from protected routes to login', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createAuthSession('unauthenticated')),
      })
    })

    await page.goto(`${BASE_URL}/#/account`)
    await page.waitForURL('**/#/login')
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })

  test('allows active sessions to mount protected routes', async ({ page }) => {
    await mockProtectedShellApis(page, 'authenticated_active')

    await page.goto(`${BASE_URL}/#/account`)
    await page.waitForURL('**/#/account')
    await expect(page.getByTestId('auth-session-header')).toBeVisible()
  })

  test('redirects grace sessions away from non-shell routes', async ({ page }) => {
    await mockProtectedShellApis(page, 'authenticated_grace')

    await page.goto(`${BASE_URL}/#/account`)
    await page.waitForURL('**/#/auth/grace')
    await expect(page.getByTestId('auth-status-grace')).toBeVisible()
  })

  test('redirects grace sessions from login to the workbench shell', async ({ page }) => {
    await mockProtectedShellApis(page, 'authenticated_grace')

    await page.goto(`${BASE_URL}/#/login`)
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
  })

  test('allows grace sessions to mount the restricted workbench shell', async ({ page }) => {
    await mockProtectedShellApis(page, 'authenticated_grace')

    await page.goto(`${BASE_URL}/#/creative/workbench`)
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
  })

  test('allows grace sessions to keep using the runtime dashboard manually', async ({ page }) => {
    await mockProtectedShellApis(page, 'authenticated_grace')

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
  })

  test('redirects revoked sessions to revoked shell', async ({ page }) => {
    await mockLockedShellApis(page, 'revoked')

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/auth/revoked')
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
  })

  test('redirects device mismatch sessions to device mismatch shell', async ({ page }) => {
    await mockLockedShellApis(page, 'device_mismatch')

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/auth/device-mismatch')
    await expect(page.getByTestId('auth-status-device_mismatch')).toBeVisible()
  })

  test('redirects expired sessions to expired shell', async ({ page }) => {
    await mockLockedShellApis(page, 'expired')

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/auth/expired')
    await expect(page.getByTestId('auth-status-expired')).toBeVisible()
  })
})
