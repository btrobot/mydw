import { expect, test } from '@playwright/test'

test.describe('Auth transport sync', () => {
  test('syncs machine-session state from local backend when a protected dashboard request returns 403', async ({ page }) => {
    let authSessionCalls = 0

    await page.route('**/api/auth/session', async (route) => {
      authSessionCalls += 1

      const payload =
        authSessionCalls === 1
          ? {
              auth_state: 'authenticated_active',
              remote_user_id: 'u_123',
              display_name: 'Alice',
              license_status: 'active',
              entitlements: ['dashboard:view'],
              expires_at: '2026-04-20T10:00:00',
              last_verified_at: '2026-04-14T00:00:00',
              offline_grace_until: '2026-04-21T10:00:00',
              denial_reason: null,
              device_id: 'device-1',
            }
          : {
              auth_state: 'revoked',
              remote_user_id: 'u_123',
              display_name: 'Alice',
              license_status: 'revoked',
              entitlements: [],
              expires_at: null,
              last_verified_at: '2026-04-14T00:00:00',
              offline_grace_until: null,
              denial_reason: 'revoked',
              device_id: 'device-1',
            }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(payload),
      })
    })

    await page.route('**/api/system/stats', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            error_code: 'revoked',
            message: 'Remote authorization revoked',
          },
        }),
      })
    })

    await page.route('**/api/system/logs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ total: 0, items: [] }),
      })
    })

    await page.route('**/api/tasks/stats', async (route) => {
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

    await page.route('**/api/publish/status', async (route) => {
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

    await page.goto(`/#/dashboard`)
    await page.waitForURL('**/#/auth/revoked')
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
  })

  test('syncs machine-session state from local backend when EventSource transport fails under revoked auth', async ({ page }) => {
    let authSessionCalls = 0
    const accountId = `transport_e2e_${Date.now()}`
    const mockedAccountNumericId = 901

    await page.addInitScript(() => {
      class FakeEventSource {
        onerror: ((event: Event) => void) | null = null

        constructor(_url: string) {
          window.setTimeout(() => {
            this.onerror?.(new Event('error'))
          }, 50)
        }

        addEventListener() {
          // no-op for this test double
        }

        close() {
          // no-op for this test double
        }
      }

      // @ts-expect-error test double
      window.EventSource = FakeEventSource
    })

    await page.route('**/api/auth/session', async (route) => {
      authSessionCalls += 1

      const payload =
        authSessionCalls === 1
          ? {
              auth_state: 'authenticated_active',
              remote_user_id: 'u_123',
              display_name: 'Alice',
              license_status: 'active',
              entitlements: ['dashboard:view'],
              expires_at: '2026-04-20T10:00:00',
              last_verified_at: '2026-04-14T00:00:00',
              offline_grace_until: '2026-04-21T10:00:00',
              denial_reason: null,
              device_id: 'device-1',
            }
          : {
              auth_state: 'revoked',
              remote_user_id: 'u_123',
              display_name: 'Alice',
              license_status: 'revoked',
              entitlements: [],
              expires_at: null,
              last_verified_at: '2026-04-14T00:00:00',
              offline_grace_until: null,
              denial_reason: 'revoked',
              device_id: 'device-1',
            }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(payload),
      })
    })

    await page.route(/\/api\/accounts\/?(?:\?.*)?$/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: mockedAccountNumericId,
            account_id: accountId,
            account_name: 'Transport E2E Account',
            status: 'inactive',
            last_login: null,
            created_at: '2026-04-22T08:00:00Z',
            updated_at: '2026-04-22T08:00:00Z',
            phone_masked: null,
            dewu_nickname: null,
            dewu_uid: null,
            avatar_url: null,
            tags: [],
            remark: null,
            session_expires_at: null,
          },
        ]),
      })
    })

    await page.route('**/api/accounts/preview/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_open: false,
          account_id: null,
        }),
      })
    })

    await page.goto(`/#/account`)
    await expect(page.locator('body')).toContainText(accountId)
    const row = page.locator('tr').filter({ hasText: accountId })
    await expect(row).toBeVisible({ timeout: 10000 })
    await row.locator('button').first().click()

    await page.waitForFunction(
      () => document.documentElement.dataset.authState === 'revoked',
      undefined,
      { timeout: 10000 }
    )
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
  })
})
