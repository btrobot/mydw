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
            name: 'Local FFmpeg 默认配置',
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

  await page.route(/\/api\/tasks(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 9901 }]),
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ total: 0, items: [] }),
    })
  })

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

    await page.getByRole('button', { name: '新建配置档' }).click()
    await page.locator('.ant-select').first().click()
    await page.getByText('本地 FFmpeg', { exact: true }).click()

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
})
