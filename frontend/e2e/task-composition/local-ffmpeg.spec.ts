import { expect, test, type Page } from '@playwright/test'

import { BASE_URL } from '../utils/creativeReviewMocks'

async function mockAuthenticatedShell(page: Page) {
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
        last_verified_at: '2026-04-19T10:00:00',
        offline_grace_until: '2026-04-21T10:00:00',
        denial_reason: null,
        device_id: 'device-1',
      }),
    })
  })
}

async function mockLocalFfmpegApis(page: Page) {
  await mockAuthenticatedShell(page)
  let taskListItems: Array<Record<string, unknown>> = []
  let submitCompositionCalls = 0

  const buildDraftTask = () => ({
    id: 9901,
    name: 'New local ffmpeg task',
    status: 'draft',
    task_kind: 'publish',
    account_id: null,
    account_name: null,
    profile_id: 2,
    priority: 5,
    scheduled_time: null,
    publish_time: null,
    final_video_path: null,
    upload_url: null,
    creative_item_id: null,
    creative_version_id: null,
    batch_id: 'batch-new-local-ffmpeg',
    failed_at_status: null,
    retry_count: 0,
    created_at: '2026-04-19T12:10:00Z',
    updated_at: '2026-04-19T12:10:00Z',
    video_ids: [11],
    copywriting_ids: [],
    cover_ids: [],
    audio_ids: [21],
    topic_ids: [],
    error_msg: null,
  })

  await page.route('**/api/accounts**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, account_id: 'acc-1', account_name: 'Main account', status: 'active' },
      ]),
    })
  })

  await page.route('**/api/profiles**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 2,
        items: [
          {
            id: 2,
            name: 'Local FFmpeg 默认合成配置',
            composition_mode: 'local_ffmpeg',
            is_default: true,
            coze_workflow_id: null,
            global_topic_ids: [],
            auto_retry: true,
            max_retry_count: 3,
          },
          {
            id: 3,
            name: 'Direct publish',
            composition_mode: 'none',
            is_default: false,
            coze_workflow_id: null,
            global_topic_ids: [],
            auto_retry: true,
            max_retry_count: 3,
          },
        ],
      }),
    })
  })

  await page.route('**/api/products**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 0, items: [] }),
    })
  })

  await page.route('**/api/videos**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 2,
        items: [
          { id: 11, name: 'Video A', duration: 12.5, product_name: 'Product A' },
          { id: 12, name: 'Video B', duration: 8.2, product_name: 'Product B' },
        ],
      }),
    })
  })

  await page.route('**/api/audios**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 21, name: 'Audio A', duration: 6.1 },
        { id: 22, name: 'Audio B', duration: 5.2 },
      ]),
    })
  })

  await page.route('**/api/copywritings**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 0, items: [] }),
    })
  })

  await page.route('**/api/covers**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
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

  await page.route(/\/api\/tasks\/?(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      taskListItems = [buildDraftTask()]
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(taskListItems),
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: taskListItems.length, items: taskListItems }),
    })
  })

  await page.route('**/api/tasks/batch-submit-composition', async (route) => {
    submitCompositionCalls += 1
    taskListItems = taskListItems.map((item) => ({
      ...item,
      status: 'composing',
      updated_at: '2026-04-19T12:11:00Z',
    }))
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success_count: 1,
        failed_count: 0,
        results: [{ task_id: 9901, status: 'submitted', job_id: 501 }],
      }),
    })
  })

  await page.route('**/api/tasks/9901/submit-composition', async (route) => {
    submitCompositionCalls += 1
    taskListItems = taskListItems.map((item) => ({
      ...item,
      status: 'composing',
      updated_at: '2026-04-19T12:11:00Z',
    }))
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 501,
        task_id: 9901,
        workflow_type: 'local_ffmpeg',
        workflow_id: null,
        external_job_id: null,
        status: 'processing',
        progress: 0,
        output_video_path: null,
        output_video_url: null,
        error_msg: null,
        started_at: '2026-04-19T12:11:00Z',
        completed_at: null,
        created_at: '2026-04-19T12:11:00Z',
        updated_at: '2026-04-19T12:11:00Z',
      }),
    })
  })

  await page.exposeFunction('getSubmitCompositionCalls', () => submitCompositionCalls)

  await page.route('**/api/tasks/*/composition-status', async (route) => {
    const body = {
      id: 71,
      task_id: 931,
      workflow_type: 'local_ffmpeg',
      workflow_id: null,
      external_job_id: null,
      status: 'completed',
      progress: 100,
      output_video_path: 'tmp/compositions/task-931/final.mp4',
      output_video_url: 'file:///tmp/compositions/task-931/final.mp4',
      error_msg: null,
      started_at: '2026-04-19T12:00:00Z',
      completed_at: '2026-04-19T12:00:12Z',
      created_at: '2026-04-19T12:00:00Z',
      updated_at: '2026-04-19T12:00:12Z',
    }
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) })
  })

  await page.route('**/api/tasks/931', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 931,
        name: 'Local FFmpeg task',
        status: 'ready',
        task_kind: 'publish',
        account_id: 1,
        account_name: 'Main account',
        profile_id: 2,
        priority: 5,
        scheduled_time: null,
        publish_time: null,
        final_video_path: 'tmp/compositions/task-931/final.mp4',
        upload_url: null,
        creative_item_id: 101,
        creative_version_id: 202,
        batch_id: 'batch-local-ffmpeg',
        failed_at_status: null,
        retry_count: 0,
        created_at: '2026-04-19T12:00:00Z',
        updated_at: '2026-04-19T12:00:12Z',
        video_ids: [11],
        copywriting_ids: [31],
        cover_ids: [41],
        audio_ids: [21],
        topic_ids: [51, 52],
        error_msg: null,
      }),
    })
  })
}

async function addMaterial(page: Page, tabName: '视频' | '音频', rowIndexes: number[]) {
  await page.getByRole('tab', { name: tabName }).click()
  await page.getByRole('button', { name: '手动添加' }).click()
  const dialogTitle = tabName === '视频' ? '选择视频' : '选择音频'
  const modal = page.getByRole('dialog', { name: dialogTitle })

  for (const index of rowIndexes) {
    await modal.locator('tbody .ant-checkbox-input').nth(index).click()
  }

  await modal.locator('.ant-btn-primary').click()
}

test.describe('local_ffmpeg frontend alignment', () => {
  test.beforeEach(async ({ page }) => {
    await mockLocalFfmpegApis(page)
  })

  test('shows accurate local_ffmpeg V1 guidance in profile management', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/profile-management`)

    await page.getByRole('button', { name: '新建合成配置' }).click()
    await page.locator('.ant-select').first().click()
    await page.locator('.ant-select-item-option-content', { hasText: '本地 FFmpeg' }).click()

    const guidance = page.getByTestId('profile-composition-mode-guidance')
    await expect(guidance).toContainText('当前只支持 1 个视频 + 可选 1 个音频')
    await expect(guidance).toContainText('文案、封面、话题仍作为发布层输入')
  })

  test('allows one video plus one audio in local_ffmpeg mode', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/create`)

    await expect(page.getByTestId('task-create-mode-label')).toContainText('本地 FFmpeg 合成')
    await expect(page.getByTestId('task-create-mode-guidance')).toContainText('只支持 1 个视频 + 可选 1 个音频')

    await addMaterial(page, '视频', [0])
    await addMaterial(page, '音频', [0])

    await expect(page.getByTestId('task-create-submit')).toBeEnabled()
  })

  test('front-loads multi-video and multi-audio violations for local_ffmpeg', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/create`)

    await addMaterial(page, '视频', [0, 1])

    const violations = page.getByTestId('task-create-mode-violations')
    await expect(violations).toContainText('仅支持 1 个视频输入')
    await expect(page.getByTestId('task-create-submit')).toBeDisabled()

    await page.reload()
    await addMaterial(page, '视频', [0])
    await addMaterial(page, '音频', [0, 1])

    const audioViolations = page.getByTestId('task-create-mode-violations')
    await expect(audioViolations).toContainText('仅支持 0 或 1 个音频输入')
    await expect(page.getByTestId('task-create-submit')).toBeDisabled()
  })

  test('shows workflow type, job status and final output in task detail', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/931`)

    const summary = page.getByTestId('task-detail-composition-summary')
    await expect(summary).toContainText('local_ffmpeg')
    await expect(summary).toContainText('已完成')
    await expect(summary).toContainText('tmp/compositions/task-931/final.mp4')
    await expect(summary).toContainText('file:///tmp/compositions/task-931/final.mp4')
  })

  test('guides the next step after task creation and can submit created drafts from task list', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/create`)

    await addMaterial(page, '视频', [0])
    await addMaterial(page, '音频', [0])
    await page.getByTestId('task-create-submit').click()

    await page.waitForURL('**/#/task/list')
    const summary = page.getByTestId('task-list-created-summary')
    await expect(summary).toContainText('本次创建 1 个任务')
    await expect(summary).toContainText('待合成 1 个')

    await page.getByTestId('task-list-submit-created-composition').click()
    await expect(page.getByText('已提交 1 个待合成任务')).toBeVisible()
    await expect(page.getByRole('cell', { name: '合成中' })).toBeVisible()
    await expect.poll(async () => page.evaluate(() => (window as typeof window & { getSubmitCompositionCalls: () => number }).getSubmitCompositionCalls())).toBe(1)
  })

  test('supports one-click composition submission directly from task list row', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/create`)
    await addMaterial(page, '视频', [0])
    await page.getByTestId('task-create-submit').click()
    await page.waitForURL('**/#/task/list')

    await page.getByTestId('task-list-submit-composition-9901').click()

    await expect(page.getByText('已提交合成任务')).toBeVisible()
    await expect(page.getByRole('cell', { name: '合成中' })).toBeVisible()
    await expect.poll(async () => page.evaluate(() => (window as typeof window & { getSubmitCompositionCalls: () => number }).getSubmitCompositionCalls())).toBe(1)
  })
})
