import { expect, test, type Page } from '@playwright/test'

import { mockWorkbenchLandingApis } from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'
const DEVICE_ID_STORAGE_KEY = 'mydw.auth.device_id'

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

async function mockAuthSession(page: Page, session = createSession()) {
  await page.route('**/api/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(session),
    })
  })
}

async function mockAuthStatus(page: Page, status = createStatus()) {
  await page.route('**/api/auth/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(status),
    })
  })
}

async function gotoLoginPage(page: Page) {
  await page.goto(`${BASE_URL}/#/login`)
  await expect(page.getByTestId('auth-login-page')).toBeVisible()
}

function loginForm(page: Page) {
  return {
    username: page.locator('input#username'),
    password: page.locator('input#password'),
    submit: page.locator('button[type="submit"]'),
  }
}

test.describe('Remote auth login page', () => {
  test('renders the current auth shell baseline', async ({ page }) => {
    await mockAuthSession(page)

    await gotoLoginPage(page)

    const { username, password, submit } = loginForm(page)
    const deviceId = await page.evaluate((storageKey) => window.localStorage.getItem(storageKey), DEVICE_ID_STORAGE_KEY)

    await expect(username).toBeVisible()
    await expect(password).toBeVisible()
    await expect(submit).toBeVisible()
    await expect(page.getByTestId('auth-login-device-meta')).toContainText(deviceId ?? '')
  })

  test('shows required-field validation on empty submit', async ({ page }) => {
    await mockAuthSession(page)

    await gotoLoginPage(page)
    await loginForm(page).submit.click()

    await expect(page.locator('.ant-form-item-explain-error')).toHaveCount(2)
  })

  test('submits username/password/device metadata and redirects on success', async ({ page }) => {
    await mockWorkbenchLandingApis(page, { authState: 'unauthenticated' })

    let receivedPayload: Record<string, unknown> | null = null
    await page.route('**/api/auth/login', async (route) => {
      receivedPayload = await route.request().postDataJSON()

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSession({
          auth_state: 'authenticated_active',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'active',
          entitlements: ['dashboard:view'],
          expires_at: '2026-04-20T10:00:00',
          last_verified_at: '2026-04-14T00:00:00',
          offline_grace_until: '2026-04-21T10:00:00',
          device_id: receivedPayload?.device_id ?? 'device-test-1',
        })),
      })
    })

    await gotoLoginPage(page)
    const { username, password, submit } = loginForm(page)
    await username.fill('alice')
    await password.fill('secret')
    await submit.click()

    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    expect(receivedPayload).not.toBeNull()
    expect(receivedPayload?.username).toBe('alice')
    expect(receivedPayload?.password).toBe('secret')
    expect(receivedPayload?.device_id).toBeTruthy()
    expect(receivedPayload?.client_version).toBeTruthy()
  })

  test('shows auth error messaging for invalid credentials', async ({ page }) => {
    await mockAuthSession(page)

    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error_code: 'invalid_credentials',
            message: 'Incorrect username or password',
          },
        }),
      })
    })

    await gotoLoginPage(page)
    const { username, password, submit } = loginForm(page)
    await username.fill('alice')
    await password.fill('wrong-password')
    await submit.click()

    await expect(page.getByTestId('auth-login-error-message')).toBeVisible()
    await expect(page.getByTestId('auth-login-error-message').locator('button')).toBeVisible()
  })

  test('shows refresh-required status context on the login page', async ({ page }) => {
    const session = createSession({
      auth_state: 'refresh_required',
      entitlements: ['dashboard:view'],
      denial_reason: 'network_timeout',
      device_id: 'device-refresh-001',
    })

    await mockAuthSession(page, session)
    await mockAuthStatus(page, createStatus({
      auth_state: 'refresh_required',
      is_authenticated: true,
      requires_reauth: true,
      denial_reason: 'network_timeout',
      device_id: 'device-refresh-001',
    }))

    await gotoLoginPage(page)

    await expect(page.getByTestId('auth-login-status-message')).toBeVisible()
    await expect(page.getByTestId('auth-login-device-meta')).toContainText('device-refresh-001')
  })

  test('persists the generated device id across reloads', async ({ page }) => {
    await mockAuthSession(page)

    await gotoLoginPage(page)

    const firstDeviceId = await page.evaluate(() => window.localStorage.getItem('mydw.auth.device_id'))
    expect(firstDeviceId).toBeTruthy()
    await expect(page.getByTestId('auth-login-device-meta')).toContainText(firstDeviceId ?? '')

    await page.reload()
    await expect(page.getByTestId('auth-login-page')).toBeVisible()

    const secondDeviceId = await page.evaluate(() => window.localStorage.getItem('mydw.auth.device_id'))
    expect(secondDeviceId).toBe(firstDeviceId)
    await expect(page.getByTestId('auth-login-device-meta')).toContainText(secondDeviceId ?? '')
  })

  test('keeps form controls keyboard-accessible', async ({ page }) => {
    await mockAuthSession(page)

    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, 'device-keyboard-001')
    }, DEVICE_ID_STORAGE_KEY)

    await gotoLoginPage(page)

    const { username, password, submit } = loginForm(page)

    await username.focus()
    await expect(username).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(password).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(submit).toBeFocused()
  })
})
