import { expect, test, type Page } from '@playwright/test'

const TEST_BASE_URL = process.env.E2E_BASE_URL || 'http://127.0.0.1:4174'

const creativeListPayload = {
  total: 4,
  items: [
    {
      id: 101,
      creative_no: 'CR-000101',
      title: 'Spring campaign',
      status: 'WAITING_REVIEW',
      current_version_id: 201,
      generation_error_msg: null,
      generation_failed_at: null,
      updated_at: '2026-04-16T10:00:00Z',
    },
    {
      id: 102,
      creative_no: 'CR-000102',
      title: 'Summer sale teaser',
      status: 'PENDING_INPUT',
      current_version_id: 202,
      generation_error_msg: '素材解析失败',
      generation_failed_at: '2026-04-16T09:30:00Z',
      updated_at: '2026-04-16T12:00:00Z',
    },
    {
      id: 103,
      creative_no: 'CR-000103',
      title: 'Autumn story board',
      status: 'APPROVED',
      current_version_id: 203,
      generation_error_msg: null,
      generation_failed_at: null,
      updated_at: '2026-04-16T08:00:00Z',
    },
    {
      id: 104,
      creative_no: 'CR-000104',
      title: 'Winter lookbook',
      status: 'REWORK_REQUIRED',
      current_version_id: null,
      generation_error_msg: null,
      generation_failed_at: null,
      updated_at: '2026-04-16T11:00:00Z',
    },
  ],
}

const creativeDetailPayload = {
  id: 101,
  creative_no: 'CR-000101',
  title: 'Spring campaign',
  status: 'WAITING_REVIEW',
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
        expires_at: '2026-04-20T10:00:00Z',
        last_verified_at: '2026-04-14T00:00:00Z',
        offline_grace_until: '2026-04-21T10:00:00Z',
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
      body: JSON.stringify({
        total: 2,
        items: [
          {
            id: 801,
            creative_item_id: 101,
            creative_version_id: 201,
            status: 'active',
            invalidation_reason: null,
            invalidated_at: null,
            creative_no: 'CR-000101',
            creative_title: 'Spring campaign',
            creative_status: 'WAITING_REVIEW',
            creative_current_version_id: 201,
            created_at: '2026-04-16T09:50:00Z',
            updated_at: '2026-04-16T10:00:00Z',
          },
          {
            id: 802,
            creative_item_id: 102,
            creative_version_id: 999,
            status: 'active',
            invalidation_reason: null,
            invalidated_at: null,
            creative_no: 'CR-000102',
            creative_title: 'Summer sale teaser',
            creative_status: 'PENDING_INPUT',
            creative_current_version_id: 202,
            created_at: '2026-04-16T11:50:00Z',
            updated_at: '2026-04-16T12:00:00Z',
          },
        ],
      }),
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

async function chooseAntSelectOption(page: Page, testId: string, optionText: string) {
  await page.getByTestId(testId).click()
  const option = page
    .locator('.ant-select-item-option-content')
    .filter({ hasText: optionText })
    .last()
  await expect(option).toBeVisible()
  await option.click()
}

async function chooseWorkbenchSort(page: Page, optionText: string) {
  await page.getByTestId('creative-workbench-sort-select').click()
  const option = page
    .locator('.ant-select-item-option-content')
    .filter({ hasText: optionText })
    .last()
  await expect(option).toBeVisible()
  await option.click()
}

async function expectWorkbenchOrder(page: Page, creativeIds: number[]) {
  const actions = page.locator('[data-testid^="creative-workbench-open-detail-"]')
  await expect(actions).toHaveCount(creativeIds.length)

  for (const [index, creativeId] of creativeIds.entries()) {
    await expect(actions.nth(index)).toHaveAttribute('data-testid', `creative-workbench-open-detail-${creativeId}`)
  }
}

test.describe('Creative workbench baseline', () => {
  test.beforeEach(async ({ page }) => {
    await mockCreativeApis(page)
  })

  test('shows the table-first workbench with business-first actions', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/#/creative/workbench`)

    await expect(page.locator('body')).toContainText('任务管理只承接执行记录、失败重试与排障')
    await expect(page.locator('body')).not.toContainText('兼容入口：新建任务')
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).toContainText('Summer sale teaser')
    await expect(page.getByTestId('creative-workbench-pool-state-101')).toContainText('已入发布池')
    await expect(page.getByTestId('creative-workbench-pool-state-102')).toContainText('版本未对齐')
    await expect(page.getByTestId('creative-workbench-open-review-101')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-ai-clip-101')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-preset-waiting_review')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-sort-select')).toBeVisible()
  })

  test('supports search and filtering before entering detail', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/#/creative/workbench`)

    await page.getByTestId('creative-workbench-search-input').fill('Spring')
    await page.getByRole('button', { name: '应用筛选' }).click()

    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')

    await page.getByTestId('creative-workbench-open-detail-101').click()

    await page.waitForURL(/#\/creative\/101\?returnTo=/)
    await expect(page.getByTestId('creative-open-task-diagnostics')).toBeVisible()
    await expect(page.locator('body')).toContainText('执行记录')
    await expect(page.locator('body')).not.toContainText('任务诊断入口')
    await page.getByText('发布运行态', { exact: true }).click()
    await expect(page.getByTestId('creative-publish-diagnostics')).toBeVisible()

    await page.getByTestId('creative-open-task-diagnostics').click()
    await page.waitForURL(/#\/task\/901\?returnTo=/)
    await expect(page.getByTestId('task-detail-page')).toBeVisible()
    await expect(page.getByTestId('task-detail-back-to-list')).toBeVisible()
  })

  test('persists applied workbench state after refresh', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/#/creative/workbench`)

    await page.getByTestId('creative-workbench-search-input').fill('Spring')
    await chooseAntSelectOption(page, 'creative-workbench-status-filter', '待审核')
    await chooseAntSelectOption(page, 'creative-workbench-pool-filter', '已入发布池')
    await page.getByRole('button', { name: '应用筛选' }).click()

    await expect(page).toHaveURL(/keyword=Spring/)
    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/poolState=in_pool/)
    await expect(page).toHaveURL(/sort=updated_desc/)
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')

    await page.reload()

    await expect(page).toHaveURL(/keyword=Spring/)
    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/poolState=in_pool/)
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')
  })

  test('returns to the filtered workbench state after entering detail', async ({ page }) => {
    await page.goto(
      `${TEST_BASE_URL}/#/creative/workbench?keyword=Spring&status=WAITING_REVIEW&poolState=in_pool&sort=updated_desc&page=1&pageSize=10`,
    )

    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')

    await page.getByTestId('creative-workbench-open-detail-101').click()

    await page.waitForURL(/#\/creative\/101\?returnTo=/)
    await page.locator('.ant-page-header-back-button').click()

    await page.waitForURL(/#\/creative\/workbench\?keyword=Spring&status=WAITING_REVIEW&poolState=in_pool&sort=updated_desc&page=1&pageSize=10/)
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')
  })

  test('supports preset views for high-frequency queues', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/#/creative/workbench`)

    await page.getByTestId('creative-workbench-preset-recent_failures').click()

    await expect(page).toHaveURL(/preset=recent_failures/)
    await expect(page).toHaveURL(/sort=failed_desc/)
    await expect(page.locator('body')).toContainText('Summer sale teaser')
    await expect(page.locator('body')).not.toContainText('Spring campaign')
    await expectWorkbenchOrder(page, [102])
  })

  test('supports explicit workbench sort views', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/#/creative/workbench`)

    await chooseWorkbenchSort(page, '待处理优先')

    await expect(page).toHaveURL(/sort=attention_desc/)
    await expectWorkbenchOrder(page, [102, 104, 101, 103])
  })

  test('shows an explicit error state when the workbench list request fails', async ({ page }) => {
    await page.unroute('**/api/creatives?**')
    await page.route('**/api/creatives?**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'boom' }),
      })
    })

    await page.goto(`${TEST_BASE_URL}/#/creative/workbench`)

    await expect(page.getByTestId('creative-workbench-error')).toBeVisible()
    await expect(page.locator('body')).toContainText('作品列表暂时不可用')
  })

  test('shows an explicit error state when the detail request fails', async ({ page }) => {
    await page.unroute('**/api/creatives/101')
    await page.route('**/api/creatives/101', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'boom' }),
      })
    })

    await page.goto(`${TEST_BASE_URL}/#/creative/101`)

    await expect(page.getByTestId('creative-detail-error')).toBeVisible()
    await expect(page.locator('body')).toContainText('作品详情暂时无法加载')
  })
})
