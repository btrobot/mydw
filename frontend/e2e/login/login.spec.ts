import { expect, test, type Page } from '@playwright/test'

import { mockWorkbenchLandingApis } from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || ''
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
  await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('auth-login-page')).toBeVisible()
}

function loginForm(page: Page) {
  return {
    username: page.locator('input#username'),
    password: page.locator('input#password'),
    rememberMe: page.getByTestId('auth-login-remember-me'),
    submit: page.locator('button[type="submit"]'),
  }
}

test.describe('Remote auth login page', () => {
  test('renders a user-facing login shell with display-only remember me and folded diagnostics by default', async ({ page }) => {
    await mockAuthSession(page)
    await mockAuthStatus(page)
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, 'device-shell-001')
    }, DEVICE_ID_STORAGE_KEY)

    await gotoLoginPage(page)

    const { username, password, rememberMe, submit } = loginForm(page)

    await expect(page.getByRole('heading', { name: '登录作品工作台' })).toBeVisible()
    await expect(page.getByText('继续处理作品、审核与 AIClip 流程。')).toBeVisible()
    await expect(username).toBeVisible()
    await expect(password).toBeVisible()
    await expect(rememberMe).toBeVisible()
    await expect(page.getByTestId('auth-login-remember-me-hint')).toContainText('不会改变设备绑定、会话有效期或后端登录策略')
    await expect(submit).toBeVisible()
    await expect(page.getByTestId('auth-login-diagnostics-trigger')).toBeVisible()
    await expect(page.getByTestId('auth-login-diagnostics-trigger')).toHaveText('查看诊断信息')
    await expect(page.getByTestId('auth-login-device-meta')).toBeHidden()
    await expect(page.getByRole('link', { name: /忘记密码|需要帮助|联系支持/ })).toHaveCount(0)
  })

  test('shows required-field validation on empty submit', async ({ page }) => {
    await mockAuthSession(page)
    await mockAuthStatus(page)

    await gotoLoginPage(page)
    await loginForm(page).submit.click()

    await expect(page.locator('.ant-form-item-explain-error')).toHaveCount(2)
  })

  test('submits username/password/device metadata only and redirects on success', async ({ page }) => {
    await mockWorkbenchLandingApis(page, { authState: 'unauthenticated' })
    await mockAuthStatus(page)

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
    const { username, password, rememberMe, submit } = loginForm(page)
    await username.fill('alice')
    await password.fill('secret')
    await rememberMe.click()
    await submit.click()

    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    expect(receivedPayload).not.toBeNull()
    expect(receivedPayload?.username).toBe('alice')
    expect(receivedPayload?.password).toBe('secret')
    expect(receivedPayload?.device_id).toBeTruthy()
    expect(receivedPayload?.client_version).toBeTruthy()
    expect(receivedPayload).not.toHaveProperty('rememberMe')
    expect(receivedPayload).not.toHaveProperty('remember_me')
  })

  test('shows auth error messaging for invalid credentials without redirecting away from login', async ({ page }) => {
    await mockAuthSession(page)
    await mockAuthStatus(page)

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
    await expect(page.getByTestId('auth-login-error-message')).toContainText('账号或密码错误')
    await expect(page.getByTestId('auth-login-error-message')).toContainText('请检查账号和密码后重新提交。')
    await expect(page.locator('.ant-message-notice')).toHaveCount(0)
    await expect(page).toHaveURL(/#\/login$/)
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })

  test('prioritizes submit errors over existing login state hints', async ({ page }) => {
    const session = createSession({
      auth_state: 'refresh_required',
      denial_reason: 'network_timeout',
      device_id: 'device-refresh-submit-001',
    })

    await mockAuthSession(page, session)
    await mockAuthStatus(page, createStatus({
      auth_state: 'refresh_required',
      is_authenticated: true,
      requires_reauth: true,
      denial_reason: 'network_timeout',
      device_id: 'device-refresh-submit-001',
    }))

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
    await expect(page.getByTestId('auth-login-status-message')).toHaveCount(0)
    await expect(page.getByTestId('auth-login-status-sync')).toHaveCount(0)
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
    await expect(page.getByTestId('auth-login-status-message')).toContainText('需要重新确认登录状态')
    await expect(page.getByTestId('auth-login-status-message')).toContainText('请重新登录或稍后重试')
  })

  test('prioritizes the login state hint over status-sync feedback', async ({ page }) => {
    const session = createSession({
      auth_state: 'refresh_required',
      entitlements: ['dashboard:view'],
      denial_reason: 'network_timeout',
      device_id: 'device-refresh-sync-001',
    })

    await mockAuthSession(page, session)
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

    await gotoLoginPage(page)

    await expect(page.getByTestId('auth-login-status-message')).toBeVisible()
    await expect(page.getByTestId('auth-login-status-sync')).toHaveCount(0)
  })

  test('keeps login diagnostics folded until expanded', async ({ page }) => {
    await mockAuthSession(page)
    await mockAuthStatus(page)

    await gotoLoginPage(page)
    const deviceId = await page.evaluate((storageKey) => window.localStorage.getItem(storageKey), DEVICE_ID_STORAGE_KEY)

    await expect(page.getByTestId('auth-login-device-meta')).toBeHidden()
    await page.getByTestId('auth-login-diagnostics-trigger').click()
    await expect(page.getByTestId('auth-login-device-meta')).toBeVisible()
    await expect(page.getByTestId('auth-login-device-meta')).toContainText(deviceId ?? '')
    await expect(page.getByTestId('auth-login-device-meta')).toContainText('0.2.0')
  })

  test('persists the generated device id across reloads', async ({ page }) => {
    await mockAuthSession(page)
    await mockAuthStatus(page)

    await gotoLoginPage(page)

    const firstDeviceId = await page.evaluate(() => window.localStorage.getItem('mydw.auth.device_id'))
    expect(firstDeviceId).toBeTruthy()
    await page.getByTestId('auth-login-diagnostics-trigger').click()
    await expect(page.getByTestId('auth-login-device-meta')).toContainText(firstDeviceId ?? '')

    await page.reload()
    await expect(page.getByTestId('auth-login-page')).toBeVisible()

    const secondDeviceId = await page.evaluate(() => window.localStorage.getItem('mydw.auth.device_id'))
    expect(secondDeviceId).toBe(firstDeviceId)
    await page.getByTestId('auth-login-diagnostics-trigger').click()
    await expect(page.getByTestId('auth-login-device-meta')).toContainText(secondDeviceId ?? '')
  })

  test('keeps form controls keyboard-accessible', async ({ page }) => {
    await mockAuthSession(page)
    await mockAuthStatus(page)

    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, 'device-keyboard-001')
    }, DEVICE_ID_STORAGE_KEY)

    await gotoLoginPage(page)

    const { username, password, rememberMe, submit } = loginForm(page)

    await username.focus()
    await expect(username).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(password).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(rememberMe).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(submit).toBeFocused()
  })
})
