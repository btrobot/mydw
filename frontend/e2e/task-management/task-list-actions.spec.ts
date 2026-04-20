import { expect, test, type Page } from '@playwright/test'

import { BASE_URL } from '../utils/creativeReviewMocks'

type MockTask = {
  id: number
  name: string
  status: 'draft' | 'composing' | 'ready' | 'failed' | 'uploaded' | 'cancelled'
  task_kind: 'publish'
  account_id: number | null
  account_name: string | null
  profile_id: number | null
  priority: number
  scheduled_time: string | null
  publish_time: string | null
  final_video_path: string | null
  upload_url: string | null
  creative_item_id: number | null
  creative_version_id: number | null
  batch_id: string | null
  failed_at_status: string | null
  retry_count: number
  created_at: string
  updated_at: string
  video_ids: number[]
  copywriting_ids: number[]
  cover_ids: number[]
  audio_ids: number[]
  topic_ids: number[]
  error_msg: string | null
}

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

async function mockTaskListApis(page: Page) {
  await mockAuthenticatedShell(page)

  const tasks: MockTask[] = [
    {
      id: 1001,
      name: 'Draft task',
      status: 'draft',
      task_kind: 'publish',
      account_id: null,
      account_name: null,
      profile_id: 1,
      priority: 5,
      scheduled_time: null,
      publish_time: null,
      final_video_path: null,
      upload_url: null,
      creative_item_id: null,
      creative_version_id: null,
      batch_id: 'batch-1',
      failed_at_status: null,
      retry_count: 0,
      created_at: '2026-04-20T10:00:00Z',
      updated_at: '2026-04-20T10:00:00Z',
      video_ids: [11],
      copywriting_ids: [],
      cover_ids: [],
      audio_ids: [],
      topic_ids: [],
      error_msg: null,
    },
    {
      id: 1002,
      name: 'Composing task',
      status: 'composing',
      task_kind: 'publish',
      account_id: 1,
      account_name: 'Main account',
      profile_id: 1,
      priority: 5,
      scheduled_time: null,
      publish_time: null,
      final_video_path: null,
      upload_url: null,
      creative_item_id: null,
      creative_version_id: null,
      batch_id: 'batch-2',
      failed_at_status: null,
      retry_count: 0,
      created_at: '2026-04-20T10:00:00Z',
      updated_at: '2026-04-20T10:00:00Z',
      video_ids: [12],
      copywriting_ids: [],
      cover_ids: [],
      audio_ids: [],
      topic_ids: [],
      error_msg: null,
    },
    {
      id: 1003,
      name: 'Ready task',
      status: 'ready',
      task_kind: 'publish',
      account_id: 1,
      account_name: 'Main account',
      profile_id: 1,
      priority: 5,
      scheduled_time: null,
      publish_time: null,
      final_video_path: 'tmp/output.mp4',
      upload_url: null,
      creative_item_id: null,
      creative_version_id: null,
      batch_id: 'batch-3',
      failed_at_status: null,
      retry_count: 0,
      created_at: '2026-04-20T10:00:00Z',
      updated_at: '2026-04-20T10:00:00Z',
      video_ids: [13],
      copywriting_ids: [],
      cover_ids: [],
      audio_ids: [],
      topic_ids: [],
      error_msg: null,
    },
    {
      id: 1004,
      name: 'Failed task',
      status: 'failed',
      task_kind: 'publish',
      account_id: 1,
      account_name: 'Main account',
      profile_id: 1,
      priority: 5,
      scheduled_time: null,
      publish_time: null,
      final_video_path: null,
      upload_url: null,
      creative_item_id: null,
      creative_version_id: null,
      batch_id: 'batch-4',
      failed_at_status: 'ready',
      retry_count: 1,
      created_at: '2026-04-20T10:00:00Z',
      updated_at: '2026-04-20T10:00:00Z',
      video_ids: [14],
      copywriting_ids: [],
      cover_ids: [],
      audio_ids: [],
      topic_ids: [],
      error_msg: 'upload failed',
    },
    {
      id: 1005,
      name: 'Uploaded task',
      status: 'uploaded',
      task_kind: 'publish',
      account_id: 1,
      account_name: 'Main account',
      profile_id: 1,
      priority: 5,
      scheduled_time: null,
      publish_time: '2026-04-20T10:00:00Z',
      final_video_path: 'tmp/output-finished.mp4',
      upload_url: 'https://example.com/video',
      creative_item_id: null,
      creative_version_id: null,
      batch_id: 'batch-5',
      failed_at_status: null,
      retry_count: 0,
      created_at: '2026-04-20T10:00:00Z',
      updated_at: '2026-04-20T10:00:00Z',
      video_ids: [15],
      copywriting_ids: [],
      cover_ids: [],
      audio_ids: [],
      topic_ids: [],
      error_msg: null,
    },
  ]

  const findTask = (taskId: number) => tasks.find((task) => task.id === taskId)

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
        total: 1,
        items: [
          {
            id: 1,
            name: 'Default profile',
            composition_mode: 'local_ffmpeg',
            is_default: true,
            coze_workflow_id: null,
            global_topic_ids: [],
            auto_retry: true,
            max_retry_count: 3,
          },
        ],
      }),
    })
  })

  await page.route(/\/api\/tasks\/?(?:\?.*)?$/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: tasks.length, items: tasks }),
    })
  })

  await page.route('**/api/tasks/1001/submit-composition', async (route) => {
    const task = findTask(1001)
    if (task) task.status = 'composing'
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 501,
        task_id: 1001,
        workflow_type: 'local_ffmpeg',
        workflow_id: null,
        external_job_id: null,
        status: 'processing',
        progress: 0,
        output_video_path: null,
        output_video_url: null,
        error_msg: null,
        started_at: '2026-04-20T10:05:00Z',
        completed_at: null,
        created_at: '2026-04-20T10:05:00Z',
        updated_at: '2026-04-20T10:05:00Z',
      }),
    })
  })

  await page.route('**/api/tasks/1002/cancel-composition', async (route) => {
    const task = findTask(1002)
    if (task) task.status = 'draft'
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 502,
        task_id: 1002,
        workflow_type: 'local_ffmpeg',
        workflow_id: null,
        external_job_id: null,
        status: 'cancelled',
        progress: 20,
        output_video_path: null,
        output_video_url: null,
        error_msg: null,
        started_at: '2026-04-20T10:05:00Z',
        completed_at: '2026-04-20T10:06:00Z',
        created_at: '2026-04-20T10:05:00Z',
        updated_at: '2026-04-20T10:06:00Z',
      }),
    })
  })

  await page.route('**/api/tasks/1003/publish', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, message: '任务已添加到发布队列' }),
    })
  })

  await page.route('**/api/tasks/1004/retry', async (route) => {
    const task = findTask(1004)
    if (task) task.status = 'ready'
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(findTask(1004)),
    })
  })

  await page.route('**/api/tasks/1004/edit-retry', async (route) => {
    const task = findTask(1004)
    if (task) task.status = 'draft'
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(findTask(1004)),
    })
  })

  await page.route(/\/api\/tasks\/\d+$/, async (route) => {
    if (route.request().method() !== 'DELETE') {
      await route.continue()
      return
    }

    const taskId = Number(route.request().url().split('/').pop())
    const index = tasks.findIndex((task) => task.id === taskId)
    if (index >= 0) tasks.splice(index, 1)
    await route.fulfill({ status: 204, body: '' })
  })
}

test.describe('task list action column', () => {
  test.beforeEach(async ({ page }) => {
    await mockTaskListApis(page)
  })

  test('shows a status-specific primary action for each row', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/list`)

    await expect(page.getByTestId('task-list-submit-composition-1001')).toBeVisible()
    await expect(page.getByTestId('task-list-open-detail-1002')).toBeVisible()
    await expect(page.getByTestId('task-list-publish-1003')).toBeVisible()
    await expect(page.getByTestId('task-list-retry-1004')).toBeVisible()
    await expect(page.getByTestId('task-list-open-detail-1005')).toBeVisible()
  })

  test('supports forward and corrective actions from the action column', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/list`)

    await page.getByTestId('task-list-publish-1003').click()
    await expect(page.getByText('已加入发布队列')).toBeVisible()

    await page.getByTestId('task-list-retry-1004').click()
    await expect(page.getByText('已发起快速重试')).toBeVisible()
    await expect(page.locator('tbody tr').filter({ hasText: 'Failed task' }).getByText('待上传')).toBeVisible()

    await page.getByTestId('task-list-more-actions-1002').click()
    await page.getByText('取消合成').click()
    await page.getByRole('button', { name: '确认取消' }).click()
    await expect(page.getByText('已取消合成，任务已回到待合成')).toBeVisible()
    await expect(page.getByTestId('task-list-submit-composition-1002')).toBeVisible()
  })
})
