import type { Page } from '@playwright/test'

export type AuthShellState =
  | 'unauthenticated'
  | 'authenticated_active'
  | 'authenticated_grace'
  | 'revoked'

interface WorkbenchLandingMockOptions {
  authState?: AuthShellState
  sessionOverrides?: Record<string, unknown>
  creativeListOverrides?: Partial<{
    total: number
    items: Array<Record<string, unknown>>
  }>
  publishStatusOverrides?: Record<string, unknown>
  scheduleConfigOverrides?: Record<string, unknown>
  poolItems?: Array<Record<string, unknown>>
}

export function createAuthSession(
  authState: AuthShellState,
  overrides: Record<string, unknown> = {},
) {
  if (authState === 'unauthenticated') {
    return {
      auth_state: 'unauthenticated',
      entitlements: [],
      denial_reason: null,
      device_id: null,
      ...overrides,
    }
  }

  if (authState === 'revoked') {
    return {
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
      ...overrides,
    }
  }

  return {
    auth_state: authState,
    remote_user_id: 'u_123',
    display_name: 'Alice',
    license_status: 'active',
    entitlements: ['dashboard:view'],
    expires_at: authState === 'authenticated_active' ? '2026-04-20T10:00:00' : null,
    last_verified_at: '2026-04-14T00:00:00',
    offline_grace_until: '2026-04-21T10:00:00',
    denial_reason: authState === 'authenticated_grace' ? 'network_timeout' : null,
    device_id: 'device-1',
    ...overrides,
  }
}

export async function mockWorkbenchLandingApis(
  page: Page,
  {
    authState = 'authenticated_active',
    sessionOverrides = {},
    creativeListOverrides = {},
    publishStatusOverrides = {},
    scheduleConfigOverrides = {},
    poolItems = [],
  }: WorkbenchLandingMockOptions = {},
) {
  await page.route('**/api/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createAuthSession(authState, sessionOverrides)),
    })
  })

  await page.route('**/api/creatives?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 1,
        items: [
          {
            id: 101,
            creative_no: 'CR-000101',
            title: 'Spring campaign',
            status: 'PENDING_INPUT',
            current_version_id: 201,
            generation_error_msg: null,
            generation_failed_at: null,
            updated_at: '2026-04-17T10:00:00Z',
          },
        ],
        ...creativeListOverrides,
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
        scheduler_mode: 'task',
        effective_scheduler_mode: 'task',
        publish_pool_kill_switch: false,
        publish_pool_shadow_read: false,
        scheduler_shadow_diff: null,
        ...publishStatusOverrides,
      }),
    })
  })

  await page.route('**/api/schedule-config', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        name: 'default',
        start_hour: 8,
        end_hour: 23,
        interval_minutes: 30,
        max_per_account_per_day: 20,
        shuffle: false,
        auto_start: true,
        publish_scheduler_mode: 'task',
        publish_pool_kill_switch: false,
        publish_pool_shadow_read: false,
        created_at: '2026-04-17T10:00:00Z',
        updated_at: '2026-04-17T10:00:00Z',
        ...scheduleConfigOverrides,
      }),
    })
  })

  await page.route('**/api/creative-publish-pool**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: poolItems.length,
        items: poolItems,
      }),
    })
  })
}

export async function mockDashboardRuntimeApis(page: Page) {
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
      body: JSON.stringify({ items: [] }),
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
}
