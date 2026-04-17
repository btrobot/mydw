import { expect, test, type Page } from '@playwright/test'

import {
  createAuthSession,
  mockDashboardRuntimeApis,
  mockWorkbenchLandingApis,
} from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'

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
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createAuthSession('revoked')),
      })
    })

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/auth/revoked')
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
  })
})
