import { expect, test } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || ''

const ACTIVE_SESSION = {
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

test.describe('Auth admin', () => {
  test('shows admin page sessions', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_SESSION),
      })
    })

    await page.route('**/api/admin/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            session_id: 1,
            auth_state: 'authenticated_active',
            remote_user_id: 'u_123',
            display_name: 'Alice',
            license_status: 'active',
            device_id: 'device-1',
            denial_reason: null,
            expires_at: '2026-04-20T10:00:00',
            last_verified_at: '2026-04-14T00:00:00',
            offline_grace_until: '2026-04-21T10:00:00',
            has_access_token: true,
            has_refresh_token: true,
            is_current_session: true,
            created_at: '2026-04-14T00:00:00',
            updated_at: '2026-04-14T00:10:00',
          },
        ]),
      })
    })

    await page.goto(`${BASE_URL}/#/settings/auth-admin`)
    await expect(page.getByTestId('auth-admin-page')).toBeVisible()
    await expect(page.getByTestId('auth-admin-session-list')).toBeVisible()
    await expect(page.locator('body')).toContainText('Alice')
    await expect(page.locator('body')).toContainText('Current session')
  })

  test('admin can revoke session', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_SESSION),
      })
    })

    await page.route('**/api/admin/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            session_id: 1,
            auth_state: 'authenticated_active',
            remote_user_id: 'u_123',
            display_name: 'Alice',
            license_status: 'active',
            device_id: 'device-1',
            denial_reason: null,
            expires_at: '2026-04-20T10:00:00',
            last_verified_at: '2026-04-14T00:00:00',
            offline_grace_until: '2026-04-21T10:00:00',
            has_access_token: true,
            has_refresh_token: true,
            is_current_session: true,
            created_at: '2026-04-14T00:00:00',
            updated_at: '2026-04-14T00:10:00',
          },
        ]),
      })
    })

    await page.route('**/api/admin/sessions/1/revoke', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          revoked_session: {
            session_id: 1,
            auth_state: 'revoked',
            remote_user_id: 'u_123',
            display_name: 'Alice',
            license_status: 'active',
            device_id: 'device-1',
            denial_reason: 'admin_revoked',
            expires_at: '2026-04-20T10:00:00',
            last_verified_at: '2026-04-14T00:00:00',
            offline_grace_until: '2026-04-21T10:00:00',
            has_access_token: false,
            has_refresh_token: false,
            is_current_session: true,
            created_at: '2026-04-14T00:00:00',
            updated_at: '2026-04-14T00:20:00',
          },
          current_session: {
            auth_state: 'revoked',
            remote_user_id: 'u_123',
            display_name: 'Alice',
            license_status: 'active',
            entitlements: ['dashboard:view'],
            expires_at: '2026-04-20T10:00:00',
            last_verified_at: '2026-04-14T00:00:00',
            offline_grace_until: '2026-04-21T10:00:00',
            denial_reason: 'admin_revoked',
            device_id: 'device-1',
          },
        }),
      })
    })

    await page.route('**/api/auth/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          auth_state: 'revoked',
          remote_user_id: 'u_123',
          display_name: 'Alice',
          license_status: 'active',
          device_id: 'device-1',
          denial_reason: 'admin_revoked',
          expires_at: '2026-04-20T10:00:00',
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
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/settings/auth-admin`)
    await page.getByRole('button', { name: 'Revoke' }).click()
    await page.waitForURL('**/#/auth/revoked')
    await expect(page.getByTestId('auth-status-revoked')).toBeVisible()
  })

  test('revoking a historical session keeps the current admin page active', async ({ page }) => {
    await page.route('**/api/auth/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_SESSION),
      })
    })

    await page.route('**/api/admin/sessions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            session_id: 1,
            auth_state: 'authenticated_active',
            remote_user_id: 'u_legacy',
            display_name: 'Legacy Session',
            license_status: 'active',
            device_id: 'device-old',
            denial_reason: null,
            expires_at: '2026-04-20T10:00:00',
            last_verified_at: '2026-04-14T00:00:00',
            offline_grace_until: '2026-04-21T10:00:00',
            has_access_token: false,
            has_refresh_token: false,
            is_current_session: false,
            created_at: '2026-04-10T00:00:00',
            updated_at: '2026-04-10T00:10:00',
          },
          {
            session_id: 2,
            auth_state: 'authenticated_active',
            remote_user_id: 'u_123',
            display_name: 'Alice',
            license_status: 'active',
            device_id: 'device-1',
            denial_reason: null,
            expires_at: '2026-04-20T10:00:00',
            last_verified_at: '2026-04-14T00:00:00',
            offline_grace_until: '2026-04-21T10:00:00',
            has_access_token: true,
            has_refresh_token: true,
            is_current_session: true,
            created_at: '2026-04-14T00:00:00',
            updated_at: '2026-04-14T00:10:00',
          },
        ]),
      })
    })

    await page.route('**/api/admin/sessions/1/revoke', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          revoked_session: {
            session_id: 1,
            auth_state: 'revoked',
            remote_user_id: 'u_legacy',
            display_name: 'Legacy Session',
            license_status: 'active',
            device_id: 'device-old',
            denial_reason: 'admin_revoked',
            expires_at: '2026-04-20T10:00:00',
            last_verified_at: '2026-04-14T00:00:00',
            offline_grace_until: '2026-04-21T10:00:00',
            has_access_token: false,
            has_refresh_token: false,
            is_current_session: false,
            created_at: '2026-04-10T00:00:00',
            updated_at: '2026-04-14T00:20:00',
          },
          current_session: ACTIVE_SESSION,
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/settings/auth-admin`)
    await page.getByRole('button', { name: 'Revoke' }).first().click()
    await expect(page.getByTestId('auth-admin-page')).toBeVisible()
    await expect(page.locator('body')).toContainText('Legacy Session')
    await expect(page.locator('body')).toContainText('Alice')
  })
})
