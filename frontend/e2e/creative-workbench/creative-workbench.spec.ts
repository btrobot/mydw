import { expect, test, type Page } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:4173'

const creativeListPayload = {
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
      updated_at: '2026-04-16T10:00:00Z',
    },
  ],
}

const creativeDetailPayload = {
  id: 101,
  creative_no: 'CR-000101',
  title: 'Spring campaign',
  status: 'PENDING_INPUT',
  current_version_id: 201,
  current_version: {
    id: 201,
    version_no: 1,
    title: 'Initial version',
    package_record_id: 301,
  },
  versions: [],
  review_summary: {
    current_version_id: null,
    current_check: null,
    total_checks: 0,
  },
  linked_task_ids: [901],
  updated_at: '2026-04-16T10:00:00Z',
}

const taskDetailPayload = {
  id: 901,
  name: 'Phase D diagnostics task',
  status: 'draft',
  account_id: 1,
  account_name: 'Creative Task Account',
  profile_id: null,
  priority: 0,
  scheduled_time: null,
  final_video_path: null,
  upload_url: null,
  creative_item_id: 101,
  creative_version_id: 201,
  created_at: '2026-04-16T10:00:00Z',
  updated_at: '2026-04-16T10:00:00Z',
  video_ids: [],
  copywriting_ids: [],
  cover_ids: [],
  audio_ids: [],
  topic_ids: [],
}

const scheduleConfigPayload = {
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
  created_at: '2026-04-16T10:00:00Z',
  updated_at: '2026-04-16T10:00:00Z',
}

const publishStatusPayload = {
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
}

async function mockCreativeApis(page: Page) {
  await page.route('**/api/auth/session', async (route) => {
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
        device_id: 'device-1',
      }),
    })
  })

  await page.route('**/api/creatives?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(creativeListPayload),
    })
  })

  await page.route('**/api/creatives/101', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(creativeDetailPayload),
    })
  })

  await page.route('**/api/publish/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(publishStatusPayload),
    })
  })

  await page.route('**/api/schedule-config', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(scheduleConfigPayload),
    })
  })

  await page.route('**/api/creative-publish-pool**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 0, items: [] }),
    })
  })

  await page.route('**/api/accounts**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1,
          account_id: 'creative-task-account',
          account_name: 'Creative Task Account',
          status: 'active',
        },
      ]),
    })
  })

  await page.route('**/api/profiles**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 0, items: [] }),
    })
  })

  await page.route('**/api/tasks/901/composition-status', async (route) => {
    await route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'composition job not found' }),
    })
  })

  await page.route('**/api/tasks/901', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(taskDetailPayload),
    })
  })

  await page.route('**/api/tasks?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 0, items: [] }),
    })
  })
}

test.describe('Creative workbench baseline', () => {
  test.beforeEach(async ({ page }) => {
    await mockCreativeApis(page)
  })

  test('shows workbench list and the default-entry banner', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/workbench`)

    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
    await expect(page.locator('body')).toContainText('CR-000101')
    await expect(page.getByTestId('creative-workbench-pool-state-101')).toContainText('Not in publish pool')
  })

  test('navigates from workbench to detail and task diagnostics', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/workbench`)
    await page.getByTestId('creative-workbench-open-detail-101').click()

    await page.waitForURL('**/#/creative/101')
    await expect(page.getByTestId('creative-publish-diagnostics')).toBeVisible()
    await expect(page.getByTestId('creative-open-task-diagnostics')).toBeVisible()

    await page.getByTestId('creative-open-task-diagnostics').click()
    await page.waitForURL('**/#/task/901')
    await expect(page.getByTestId('task-detail-diagnostics-banner')).toBeVisible()
  })
})
