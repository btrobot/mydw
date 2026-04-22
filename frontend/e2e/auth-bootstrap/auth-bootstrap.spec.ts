import { expect, test } from '@playwright/test'


test.describe('Auth bootstrap', () => {
  test('shows user-facing bootstrap loading state before auth session resolves', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1200))
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

    await page.goto('/')

    await expect(page.getByTestId('auth-bootstrap-loading')).toBeVisible()
    await expect(page.getByTestId('auth-bootstrap-loading-copy')).toContainText('正在准备登录环境')
    await expect(page.getByTestId('auth-bootstrap-loading-copy')).toContainText('正在检查当前登录状态，请稍候。')
    await expect(page.locator('body')).not.toContainText('Restoring local auth session')
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'ready')
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })

  test('hydrates unauthenticated machine-session state from local backend', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
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

    await page.goto('/')
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'ready')

    const authState = await page.evaluate(() => document.documentElement.dataset.authState)
    expect(authState).toBe('unauthenticated')
  })

  test('hydrates authenticated_grace machine-session state from local backend', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'authenticated_grace',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'active',
          entitlements: ['dashboard:view'],
          expires_at: null,
          last_verified_at: '2026-04-14T00:00:00',
          offline_grace_until: '2026-04-15T00:00:00',
          denial_reason: 'network_timeout',
          device_id: 'device-1',
        }),
      })
    })

    await page.goto('/')
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'ready')

    const authState = await page.evaluate(() => document.documentElement.dataset.authState)
    expect(authState).toBe('authenticated_grace')
  })

  test('shows a user-facing bootstrap warning when session restore fails', async ({ page }) => {
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

    await page.goto('/')
    await page.waitForFunction(() => document.documentElement.dataset.authBootstrapStatus === 'error')

    await expect(page.locator('body')).toContainText('暂时无法完成登录准备')
    await expect(page.locator('body')).toContainText('你仍可继续登录；如果问题持续，请稍后重新检查。')
    await expect(page.locator('body')).not.toContainText('Local auth bootstrap failed')
    await expect(page.getByRole('link', { name: /忘记密码|需要帮助|联系支持/ })).toHaveCount(0)
    await expect(page.getByTestId('auth-login-page')).toBeVisible()
  })
})
