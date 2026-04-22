import { expect, test, type Page } from '@playwright/test'

import { createAuthSession, mockWorkbenchLandingApis } from '../utils/workbenchEntryMocks'

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

const createSession = (overrides: Record<string, unknown> = {}) => ({
  auth_state: 'unauthenticated',
  entitlements: [],
  denial_reason: null,
  device_id: null,
  ...overrides,
})

const HARD_STOP_VARIANTS = ['revoked', 'device_mismatch', 'expired'] as const

const STATUS_EXPECTATIONS = {
  revoked: {
    path: '/#/auth/revoked',
    title: '访问权限已失效',
    description: '当前账号的应用访问权限已失效，请联系管理员恢复后再登录。',
  },
  device_mismatch: {
    path: '/#/auth/device-mismatch',
    title: '当前设备未通过校验',
    description: '请退出后重新登录；如果问题持续，请联系管理员重新绑定设备。',
  },
  expired: {
    path: '/#/auth/expired',
    title: '登录已过期',
    description: '当前登录已过期，请重新登录后继续使用。',
  },
  grace: {
    path: '/#/auth/grace',
    title: '宽限模式',
    description: '当前授权服务暂不可用，你仍可查看已有内容，但受保护操作会受到限制。',
  },
} as const

async function mockStatusShell(page: Page, variant: 'revoked' | 'device_mismatch' | 'expired' | 'grace') {
  const statusAuthState = variant === 'grace' ? 'authenticated_grace' : variant
  const sessionByVariant = {
    revoked: createAuthSession('revoked', {
      display_name: 'Alice',
      device_id: 'device-1',
    }),
    device_mismatch: createSession({
      auth_state: 'device_mismatch',
      display_name: 'Alice',
      device_id: 'device-1',
      denial_reason: 'device_mismatch',
    }),
    expired: createSession({
      auth_state: 'expired',
      display_name: 'Alice',
      device_id: 'device-1',
      denial_reason: 'expired',
    }),
    grace: createAuthSession('authenticated_grace', {
      display_name: 'Alice',
      device_id: 'device-1',
    }),
  } as const

  await page.route('**/api/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(sessionByVariant[variant]),
    })
  })

  await page.route('**/api/auth/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createStatus({
        auth_state: statusAuthState,
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

  await page.route('**/api/auth/logout', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createSession()),
    })
  })
}

test.describe('Auth shell pages', () => {
  test('renders login page and submits successful login to local auth surface', async ({ page }) => {
    await mockWorkbenchLandingApis(page, { authState: 'unauthenticated' })
    let currentSession = createSession()

    await page.unroute('**/api/auth/session')
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(currentSession),
      })
    })

    await page.route('**/api/auth/login', async (route) => {
      const body = await route.request().postDataJSON()
      expect(body.username).toBe('alice')
      expect(body.password).toBe('secret')
      expect(body.device_id).toBeTruthy()

      currentSession = {
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
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(currentSession),
      })
    })

    await page.goto(`/#/login`)
    await expect(page.getByTestId('auth-login-page')).toBeVisible()

    await page.locator('input#username').fill('alice')
    await page.locator('input#password').fill('secret')
    await page.locator('button[type="submit"]').click()

    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
  })

  for (const variant of HARD_STOP_VARIANTS) {
    test(`renders ${variant} shell with fixed copy and single CTA`, async ({ page }) => {
      await mockStatusShell(page, variant)
      await page.goto(`${STATUS_EXPECTATIONS[variant].path}`)

      await expect(page.getByTestId(`auth-status-${variant}`)).toBeVisible()
      await expect(page.getByTestId('auth-status-primary-alert')).toContainText(STATUS_EXPECTATIONS[variant].title)
      await expect(page.getByTestId('auth-status-primary-alert')).toContainText(STATUS_EXPECTATIONS[variant].description)
      await expect(page.getByTestId(`auth-status-live-${variant}`)).toHaveCount(0)

      const actions = page.getByTestId('auth-status-actions').getByRole('button')
      await expect(actions).toHaveCount(1)
      await expect(page.getByTestId('auth-status-signout-button')).toHaveText('重新登录')

      await expect(page.getByTestId('auth-status-session-meta')).not.toBeVisible()
      await expect(page.getByTestId('auth-status-diagnostics-trigger')).toHaveText('查看诊断信息')
      await page.getByTestId('auth-status-diagnostics-trigger').click()
      await expect(page.getByTestId('auth-status-session-meta')).toBeVisible()
      await expect(page.getByTestId('auth-status-session-meta')).toContainText('Alice')
      await expect(page.getByTestId('auth-status-session-meta')).toContainText('device-1')
    })
  }

  test('renders grace shell with dual CTA and folded diagnostics', async ({ page }) => {
    await mockStatusShell(page, 'grace')
    await page.goto(`${STATUS_EXPECTATIONS.grace.path}`)

    await expect(page.getByTestId('auth-status-grace')).toBeVisible()
    await expect(page.getByTestId('auth-status-primary-alert')).toContainText(STATUS_EXPECTATIONS.grace.title)
    await expect(page.getByTestId('auth-status-primary-alert')).toContainText(STATUS_EXPECTATIONS.grace.description)
    await expect(page.getByTestId('auth-status-live-grace')).toHaveCount(0)

    const actions = page.getByTestId('auth-status-actions').getByRole('button')
    await expect(actions).toHaveCount(2)
    await expect(page.getByRole('button', { name: '进入作品工作台' })).toBeVisible()
    await expect(page.getByTestId('auth-status-signout-button')).toHaveText('退出登录')

    await expect(page.getByTestId('auth-status-session-meta')).not.toBeVisible()
    await expect(page.getByTestId('auth-status-diagnostics-trigger')).toHaveText('查看诊断信息')
    await page.getByTestId('auth-status-diagnostics-trigger').click()
    await expect(page.getByTestId('auth-status-session-meta')).toBeVisible()
    await expect(page.getByTestId('auth-status-session-meta')).toContainText('Alice')
    await expect(page.getByTestId('auth-status-session-meta')).toContainText('device-1')
  })

  test('keeps hard-stop CTA count when live status refresh fails', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          display_name: 'Alice',
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

    await page.route('**/api/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSession()),
      })
    })

    await page.goto(`${STATUS_EXPECTATIONS.revoked.path}`)
    await expect(page.getByText('授权状态暂时无法刷新')).toBeVisible()
    await expect(page.getByRole('button', { name: '重试' })).toHaveCount(0)
    await expect(page.getByTestId('auth-status-actions').getByRole('button')).toHaveCount(1)
    await expect(page.getByTestId('auth-status-signout-button')).toHaveText('重新登录')
  })
})
