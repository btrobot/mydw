import { expect, test, type Page } from '@playwright/test'

import {
  BASE_URL,
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'

async function mockTaskDiagnosticsApis(page: Page) {
  const state = createCreativeReviewState()
  const taskDetail = {
    id: 901,
    name: 'Phase D task diagnostic',
    status: 'draft',
    account_id: 1,
    account_name: 'Creative Task Account',
    profile_id: null,
    priority: 6,
    scheduled_time: null,
    final_video_path: null,
    upload_url: null,
    creative_item_id: 101,
    creative_version_id: 202,
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

  await page.route('**/api/system-stats', async (route) => {
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

  await page.route('**/api/system-logs**', async (route) => {
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

  test('keeps dashboard as current default entry while foregrounding the creative CTA', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/`)

    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('dashboard-open-workbench')).toBeVisible()

    await page.getByTestId('dashboard-open-workbench').click()
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
  })

  test('treats task list/detail as diagnostics surfaces with return links into creative flows', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/list`)

    await expect(page.getByTestId('task-list-semantics')).toBeVisible()
    await expect(page.getByRole('cell', { name: 'Phase D task diagnostic' })).toBeVisible()
    await page.getByRole('row', { name: /901.*Phase D task diagnostic/i }).click()

    await page.waitForURL('**/#/task/901')
    await expect(page.getByTestId('task-detail-diagnostics-banner')).toBeVisible()

    await page.getByTestId('task-detail-open-creative').click()
    await page.waitForURL('**/#/creative/101')
    await expect(page.getByTestId('creative-open-task-diagnostics')).toBeVisible()

    await page.getByTestId('creative-open-task-diagnostics').click()
    await page.waitForURL('**/#/task/901')

    await page.getByTestId('task-detail-open-workbench').click()
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
  })
})
