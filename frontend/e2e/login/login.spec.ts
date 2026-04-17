import { expect, test, type Page } from '@playwright/test'

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

async function mockDashboardApis(page: Page) {
  await page.route('**/api/system/stats**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_accounts: 1,
        active_accounts: 1,
        total_products: 0,
      }),
    })
  })

  await page.route('**/api/system/logs**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 0,
        items: [],
      }),
    })
  })

  await page.route('**/api/tasks/stats**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 0,
        draft: 0,
        composing: 0,
        ready: 0,
        uploading: 0,
        uploaded: 0,
        failed: 0,
        cancelled: 0,
        today_uploaded: 0,
      }),
    })
  })

  await page.route('**/api/publish/status**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'idle',
        current_task_id: null,
        total_pending: 0,
        total_success: 0,
        total_failed: 0,
      }),
    })
  })
}

async function gotoLoginPage(page: Page) {
  await page.goto(`${BASE_URL}/#/login`)
  await expect(page.getByTestId('auth-login-page')).toBeVisible()
}

test.describe('Remote auth login page', () => {
  test('renders the current auth shell baseline', async ({ page }) => {
    await mockAuthSession(page)

    await gotoLoginPage(page)

    await expect(page.getByText('Remote Auth Login', { exact: true })).toBeVisible()
    await expect(page.getByLabel('Username')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
    await expect(page.getByText(/^Device ID:/)).toBeVisible()
  })

  test('shows required-field validation on empty submit', async ({ page }) => {
    await mockAuthSession(page)

    await gotoLoginPage(page)
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page.getByText('Please enter a username')).toBeVisible()
    await expect(page.getByText('Please enter a password')).toBeVisible()
  })

  test('submits username/password/device metadata and redirects on success', async ({ page }) => {
    await mockAuthSession(page)
    await mockDashboardApis(page)

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
    await page.getByLabel('Username').fill('alice')
    await page.getByLabel('Password').fill('secret')
    await page.getByRole('button', { name: 'Sign in' }).click()

    await page.waitForURL('**/#/dashboard')
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
    await page.getByLabel('Username').fill('alice')
    await page.getByLabel('Password').fill('wrong-password')
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page.getByTestId('auth-login-error-message')).toBeVisible()
    await expect(page.getByTestId('auth-login-error-message')).toContainText('Incorrect username or password')
    await expect(page.getByTestId('auth-login-error-message')).toContainText('Double-check your credentials and try signing in again.')
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
    await expect(page.getByTestId('auth-login-status-message')).toContainText('Session refresh required')
    await expect(page.getByTestId('auth-login-status-message')).toContainText('Reason: network_timeout.')
    await expect(page.getByText('Device ID: device-refresh-001')).toBeVisible()
  })

  test('persists the generated device id across reloads', async ({ page }) => {
    await mockAuthSession(page)

    await gotoLoginPage(page)

    const firstDeviceId = await page.evaluate(() => window.localStorage.getItem('mydw.auth.device_id'))
    expect(firstDeviceId).toBeTruthy()
    await expect(page.getByText(`Device ID: ${firstDeviceId}`)).toBeVisible()

    await page.reload()
    await expect(page.getByTestId('auth-login-page')).toBeVisible()

    const secondDeviceId = await page.evaluate(() => window.localStorage.getItem('mydw.auth.device_id'))
    expect(secondDeviceId).toBe(firstDeviceId)
    await expect(page.getByText(`Device ID: ${secondDeviceId}`)).toBeVisible()
  })

  test('keeps form controls keyboard-accessible', async ({ page }) => {
    await mockAuthSession(page)

    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, 'device-keyboard-001')
    }, DEVICE_ID_STORAGE_KEY)

    await gotoLoginPage(page)

    const username = page.getByLabel('Username')
    const password = page.getByLabel('Password')
    const submit = page.getByRole('button', { name: 'Sign in' })

    await username.focus()
    await expect(username).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(password).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(submit).toBeFocused()
  })
})
