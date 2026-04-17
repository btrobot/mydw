import { expect, test } from '@playwright/test'

import { mockWorkbenchLandingApis } from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'

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

    await page.getByLabel('Username').fill('alice')
    await page.getByLabel('Password').fill('secret')
    await page.locator('button[type="submit"]').click()

    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
  })

  test('renders revoked shell', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/auth/revoked`)
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
    await expect(page.locator('body')).toContainText('Authorization revoked')
  })

  test('renders device mismatch shell', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/auth/device-mismatch`)
    await expect(page.getByTestId('auth-status-device_mismatch')).toBeVisible()
    await expect(page.locator('body')).toContainText('Device mismatch')
  })

  test('renders expired shell', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/auth/expired`)
    await expect(page.getByTestId('auth-status-expired')).toBeVisible()
    await expect(page.locator('body')).toContainText('Session expired')
  })

  test('renders grace shell', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/auth/grace`)
    await expect(page.getByTestId('auth-status-grace')).toBeVisible()
    await expect(page.locator('body')).toContainText('Offline grace mode')
  })
})
