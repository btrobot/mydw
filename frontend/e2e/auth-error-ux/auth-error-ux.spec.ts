import { expect, test } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || ''
const ROOT_URL = BASE_URL || '/'
const BOOTSTRAP_WARNING = 'Local auth bootstrap failed, but app startup can continue.'

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

async function mockLockedShell(
  page: import('@playwright/test').Page,
  authState: 'revoked' | 'device_mismatch' | 'expired',
) {
  await page.route('**/api/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createSession({
        auth_state: authState,
        display_name: 'Alice',
        device_id: 'device-1',
        denial_reason: authState,
      })),
    })
  })

  await page.route('**/api/auth/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createStatus({
        auth_state: authState,
        remote_user_id: 'u_123',
        display_name: 'Alice',
        license_status: authState === 'revoked' ? 'revoked' : 'active',
        device_id: 'device-1',
        denial_reason: authState,
        last_verified_at: '2026-04-14T00:00:00',
        requires_reauth: true,
      })),
    })
  })
}

test.describe('Auth error UX', () => {
  test('shows a friendly login error for invalid credentials', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSession()),
      })
    })

    await page.route('**/api/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createStatus()),
      })
    })

    await page.route('**/api/auth/login', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error_code: 'invalid_credentials',
            message: 'Invalid username or password',
          },
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'domcontentloaded' })
    await page.locator('input#username').fill('alice')
    await page.locator('input#password').fill('wrong-password')
    await page.locator('button[type="submit"]').click()

    await expect(page.getByTestId('auth-login-error-message')).toBeVisible()
    await expect(page.getByTestId('auth-login-error-message')).toContainText('账号或密码错误')
    await expect(page.getByTestId('auth-login-error-message')).toContainText('请检查用户名和密码后重新提交。')
    await expect(page.locator('.ant-message-notice')).toHaveCount(0)
  })

  test('keeps a minimal state hint on the login page for generic auth errors', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSession({
          auth_state: 'error',
          denial_reason: 'network_timeout',
          device_id: 'device-error-001',
        })),
      })
    })

    await page.route('**/api/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createStatus({
          auth_state: 'error',
          denial_reason: 'network_timeout',
          device_id: 'device-error-001',
        })),
      })
    })

    await page.goto(`${BASE_URL}/#/login`, { waitUntil: 'domcontentloaded' })

    await expect(page.getByTestId('auth-login-status-message')).toBeVisible()
    await expect(page.getByTestId('auth-login-status-message')).toContainText('授权服务暂不可用')
    await expect(page.getByTestId('auth-login-status-message')).toContainText('请稍后重试')
  })

  test('shows an offline-friendly message when auth bootstrap fails', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
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

    await page.goto(ROOT_URL, { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('auth-bootstrap-error')).toBeVisible()
    await expect(page.locator('body')).toContainText(BOOTSTRAP_WARNING)
    await expect(page.getByTestId('auth-bootstrap-error').locator('button')).toBeVisible()
  })

  test('shows a re-login prompt on the revoked auth shell', async ({ page }) => {
    await mockLockedShell(page, 'revoked')
    await page.goto(`${BASE_URL}/#/auth/revoked`, { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
    await expect(page.getByTestId('auth-status-primary-alert')).toContainText('访问权限已失效')
    await expect(page.getByTestId('auth-status-live-revoked')).toBeVisible()
    await expect(page.getByTestId('auth-status-live-revoked')).toContainText('实时状态补充')
    await expect(page.getByTestId('auth-status-actions').getByRole('button')).toHaveCount(1)
    await expect(page.getByTestId('auth-status-signout-button')).toHaveText('退出登录并返回登录页')
    await expect(page.getByTestId('auth-status-session-meta')).not.toBeVisible()
  })

  test('shows fixed copy on device mismatch auth shell', async ({ page }) => {
    await mockLockedShell(page, 'device_mismatch')
    await page.goto(`${BASE_URL}/#/auth/device-mismatch`, { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('auth-status-primary-alert')).toContainText('当前设备未通过校验')
    await expect(page.getByTestId('auth-status-actions').getByRole('button')).toHaveCount(1)
  })

  test('shows fixed copy on expired auth shell', async ({ page }) => {
    await mockLockedShell(page, 'expired')
    await page.goto(`${BASE_URL}/#/auth/expired`, { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('auth-status-primary-alert')).toContainText('登录已过期')
    await expect(page.getByTestId('auth-status-actions').getByRole('button')).toHaveCount(1)
  })

  test('shows dual CTA on grace shell', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSession({
          auth_state: 'authenticated_grace',
          display_name: 'Alice',
          device_id: 'device-1',
          denial_reason: 'network_timeout',
        })),
      })
    })

    await page.route('**/api/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createStatus({
          auth_state: 'authenticated_grace',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'active',
          device_id: 'device-1',
          denial_reason: 'network_timeout',
          last_verified_at: '2026-04-14T00:00:00',
          is_authenticated: true,
          is_grace: true,
          can_read_local_data: true,
        })),
      })
    })

    await page.goto(`${BASE_URL}/#/auth/grace`, { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('auth-status-primary-alert')).toContainText('宽限模式')
    await expect(page.getByTestId('auth-status-live-grace')).toContainText('实时状态补充')
    await expect(page.getByTestId('auth-status-actions').getByRole('button')).toHaveCount(2)
    await expect(page.getByRole('button', { name: '继续进入工作台' })).toBeVisible()
    await expect(page.getByTestId('auth-status-signout-button')).toHaveText('退出登录并返回登录页')
  })
})
