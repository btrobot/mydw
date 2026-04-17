import { expect, test, type Page } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:4173'

const creativeListPayload = {
  total: 1,
  items: [
    {
      id: 101,
      creative_no: 'CR-000101',
      title: '春季作品样本',
      status: 'PENDING_INPUT',
      current_version_id: 201,
      updated_at: '2026-04-16T10:00:00',
    },
  ],
}

const creativeDetailPayload = {
  id: 101,
  creative_no: 'CR-000101',
  title: '春季作品样本',
  status: 'PENDING_INPUT',
  current_version_id: 201,
  current_version: {
    id: 201,
    version_no: 1,
    title: '初始版本',
    package_record_id: 301,
  },
  linked_task_ids: [901],
  updated_at: '2026-04-16T10:00:00',
}

const taskDetailPayload = {
  id: 901,
  name: '阶段 A 样本任务',
  status: 'draft',
  account_id: 1,
  account_name: 'Creative Task Account',
  profile_id: null,
  priority: 0,
  scheduled_time: null,
  final_video_path: null,
  upload_url: null,
  created_at: '2026-04-16T10:00:00',
  updated_at: '2026-04-16T10:00:00',
  video_ids: [],
  copywriting_ids: [],
  cover_ids: [],
  audio_ids: [],
  topic_ids: [],
}

const accountsPayload = [
  {
    id: 1,
    account_id: 'creative-task-account',
    account_name: 'Creative Task Account',
    status: 'active',
  },
]

const profilesPayload = {
  total: 0,
  items: [],
}

async function mockPhaseAApis(page: Page) {
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

  await page.route('**/api/accounts', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(accountsPayload),
    })
  })

  await page.route('**/api/accounts/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(accountsPayload),
    })
  })

  await page.route('**/api/accounts?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(accountsPayload),
    })
  })

  await page.route('**/api/accounts/?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(accountsPayload),
    })
  })

  await page.route('**/api/profiles', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(profilesPayload),
    })
  })

  await page.route('**/api/profiles/', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(profilesPayload),
    })
  })

  await page.route('**/api/profiles?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(profilesPayload),
    })
  })

  await page.route('**/api/profiles/?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(profilesPayload),
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
      body: JSON.stringify({
        total: 0,
        items: [],
      }),
    })
  })

  await page.route('**/api/tasks/?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 0,
        items: [],
      }),
    })
  })
}

test.describe('Creative workbench Phase A', () => {
  test.beforeEach(async ({ page }) => {
    await mockPhaseAApis(page)
  })

  test('opens workbench from the sidebar and shows list data', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/task/list`)
    await page.getByText('作品工作台', { exact: true }).click()
    await page.getByText('作品列表', { exact: true }).click()
    await page.waitForURL('**/#/creative/workbench')

    await expect(page.locator('body')).toContainText('作品工作台')
    await expect(page.locator('body')).toContainText('春季作品样本')
    await expect(page.locator('body')).toContainText('CR-000101')
    await expect(page.locator('body')).toContainText('当前版本 #201')
  })

  test('navigates from workbench to detail, task detail, and ai-clip diagnostics', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/workbench`)
    await page.getByRole('button', { name: '查看详情' }).click()

    await page.waitForURL('**/#/creative/101')
    await expect(page.locator('body')).toContainText('初始版本')
    await expect(page.locator('body')).toContainText('任务 #901')

    await page.getByRole('button', { name: '查看关联任务' }).click()
    await page.waitForURL('**/#/task/901')
    await expect(page.locator('body')).toContainText('任务详情 #901')

    await page.getByText('AI 剪辑', { exact: true }).click()
    await page.waitForURL('**/#/ai-clip')
    await expect(page.locator('body')).toContainText('AI 智能剪辑')
  })
})
