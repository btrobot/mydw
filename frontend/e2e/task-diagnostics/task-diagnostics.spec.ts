import { expect, test, type Page } from '@playwright/test'

import {
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'

async function mockTaskDiagnosticsApis(page: Page) {
  const state = createCreativeReviewState()
  const taskDetail = {
    id: 901,
    name: 'Phase E task diagnostic',
    status: 'draft',
    task_kind: 'publish',
    account_id: 1,
    account_name: 'Creative Task Account',
    profile_id: null,
    priority: 6,
    scheduled_time: null,
    publish_time: '2026-04-16T12:30:00Z',
    final_video_path: null,
    upload_url: null,
    creative_item_id: 101,
    creative_version_id: 202,
    batch_id: 'batch-pr2',
    failed_at_status: 'uploading',
    retry_count: 2,
    created_at: '2026-04-16T10:00:00Z',
    updated_at: '2026-04-16T10:00:00Z',
    video_ids: [],
    copywriting_ids: [],
    cover_ids: [],
    audio_ids: [],
    topic_ids: [],
  }

  await mockCreativeReviewApis(page, state, {
    taskDetails: {
      901: taskDetail,
    },
  })

  await page.route('**/api/system/stats**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_accounts: 3,
        active_accounts: 2,
        total_products: 12,
      }),
    })
  })

  await page.route('**/api/system/logs**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 1,
            created_at: '2026-04-16T10:00:00Z',
            level: 'INFO',
            module: 'dashboard',
            message: 'diagnostic ready',
          },
        ],
      }),
    })
  })

  await page.route('**/api/tasks/stats', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 1,
        draft: 1,
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

  await page.route(/\/api\/tasks\/?(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 1, items: [taskDetail] }),
    })
  })
}

test.describe('Task diagnostics positioning', () => {
  test.beforeEach(async ({ page }) => {
    await mockTaskDiagnosticsApis(page)
  })

  test('uses workbench as the default entry while keeping dashboard reachable', async ({ page }) => {
    await page.goto(`/#/`)

    await page.waitForURL(/#\/creative\/workbench/)
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()

    await page.goto(`/#/dashboard`)
    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()

    await page.getByTestId('dashboard-open-workbench').click()
    await page.waitForURL(/#\/creative\/workbench/)
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
  })

  test('treats task list/detail as diagnostics surfaces with return links into creative flows', async ({ page }) => {
    const taskRow = page.locator('tbody tr').filter({ hasText: 'Phase E task diagnostic' })

    await page.goto(`/#/task/list?status=draft&task_kind=publish&page=1&pageSize=50`)

    await expect(page.getByTestId('task-list-semantics')).toBeVisible()
    await expect(page.getByRole('cell', { name: 'Phase E task diagnostic' })).toBeVisible()
    await taskRow.click()

    await page.waitForURL('**/#/task/901?returnTo=*')
    await expect(page).toHaveURL(/#\/task\/901\?returnTo=%2Ftask%2Flist%3Fstatus%3Ddraft%26task_kind%3Dpublish%26page%3D1%26pageSize%3D50$/)
    await expect(page.getByTestId('task-detail-back-to-list')).toBeVisible()

    await page.getByTestId('task-detail-open-creative').click()
    await page.waitForURL('**/#/creative/101?taskId=901&returnTo=*')
    await expect(page.getByTestId('creative-open-advanced-diagnostics')).toBeVisible()
    await expect(page.getByTestId('creative-open-task-diagnostics')).toHaveCount(0)

    await page.getByTestId('creative-open-advanced-diagnostics').click()
    await expect(page).toHaveURL(/diagnostics=advanced/)
    await expect(page.getByTestId('creative-detail-diagnostics-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-task-diagnostics-note')).toContainText('不回写作品定义、版本结果或发布侧承接语义')
    await expect(page.getByTestId('creative-open-task-diagnostics')).toBeVisible()

    await page.getByTestId('creative-open-task-diagnostics').click()
    await expect(page).toHaveURL(/#\/task\/901\?returnTo=%2Ftask%2Flist%3Fstatus%3Ddraft%26task_kind%3Dpublish%26page%3D1%26pageSize%3D50$/)

    await page.getByTestId('task-detail-back-to-list').click()
    await expect(page).toHaveURL(/#\/task\/list\?status=draft&task_kind=publish&page=1&pageSize=50$/)
    await expect(page.getByTestId('task-list-semantics')).toBeVisible()

    await taskRow.click()
    await page.waitForURL('**/#/task/901?returnTo=*')
    await page.getByTestId('task-detail-open-workbench').click()
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
  })

  test('shows dashboard publish failures as explicit errors instead of idle state', async ({ page }) => {
    await page.unroute('**/api/publish/status**')
    await page.route('**/api/publish/status**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'publish status failed' }),
      })
    })

    await page.goto(`/#/dashboard`)

    await expect(page.getByTestId('dashboard-publish-status-error')).toBeVisible()
    await expect(page.getByTestId('dashboard-publish-status-error').locator('button')).toBeVisible()
  })
})

