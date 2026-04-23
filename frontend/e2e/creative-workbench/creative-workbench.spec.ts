import { expect, test, type Page } from '@playwright/test'

const creativeListPayload = {
  total: 4,
  summary: {
    all_count: 4,
    waiting_review_count: 1,
    pending_input_count: 1,
    needs_rework_count: 1,
    recent_failures_count: 1,
    active_pool_count: 2,
    aligned_pool_count: 1,
    version_mismatch_count: 1,
  },
  items: [
    {
      id: 101,
      creative_no: 'CR-000101',
      title: 'Spring campaign',
      status: 'WAITING_REVIEW',
      current_version_id: 201,
      subject_product_id: 301,
      subject_product_name_snapshot: 'Classic Hoodie',
      main_copywriting_text: '??????????',
      target_duration_seconds: 30,
      input_items: [
        { material_type: 'video', material_id: 11, sequence: 1, instance_no: 1, enabled: true },
      ],
      input_orchestration: {
        profile_id: 1,
        orchestration_hash: 'orchestration-101',
        item_count: 1,
        enabled_item_count: 1,
        material_counts: { video: 1, copywriting: 0, cover: 0, audio: 0, topic: 0 },
        enabled_material_counts: { video: 1, copywriting: 0, cover: 0, audio: 0, topic: 0 },
      },
      generation_error_msg: null,
      generation_failed_at: null,
      pool_state: 'in_pool',
      active_pool_item_id: 801,
      active_pool_version_id: 201,
      active_pool_aligned: true,
      updated_at: '2026-04-16T10:00:00Z',
    },
    {
      id: 102,
      creative_no: 'CR-000102',
      title: 'Summer sale teaser',
      status: 'PENDING_INPUT',
      current_version_id: 202,
      subject_product_id: 302,
      subject_product_name_snapshot: 'Runner Pro',
      main_copywriting_text: '??????????',
      target_duration_seconds: 45,
      input_items: [
        { material_type: 'video', material_id: 12, sequence: 1, instance_no: 1, enabled: true },
        { material_type: 'video', material_id: 12, sequence: 2, instance_no: 2, enabled: true },
      ],
      input_orchestration: {
        profile_id: 1,
        orchestration_hash: 'orchestration-102',
        item_count: 2,
        enabled_item_count: 2,
        material_counts: { video: 2, copywriting: 0, cover: 0, audio: 0, topic: 0 },
        enabled_material_counts: { video: 2, copywriting: 0, cover: 0, audio: 0, topic: 0 },
      },
      generation_error_msg: '??????',
      generation_failed_at: '2026-04-16T09:30:00Z',
      pool_state: 'version_mismatch',
      active_pool_item_id: 802,
      active_pool_version_id: 999,
      active_pool_aligned: false,
      updated_at: '2026-04-16T12:00:00Z',
    },
    {
      id: 103,
      creative_no: 'CR-000103',
      title: 'Autumn story board',
      status: 'APPROVED',
      current_version_id: 203,
      subject_product_id: 303,
      subject_product_name_snapshot: 'Trail Jacket',
      main_copywriting_text: '?????????????',
      target_duration_seconds: 25,
      input_items: [
        { material_type: 'video', material_id: 13, sequence: 1, instance_no: 1, enabled: true },
      ],
      input_orchestration: {
        profile_id: 1,
        orchestration_hash: 'orchestration-103',
        item_count: 1,
        enabled_item_count: 1,
        material_counts: { video: 1, copywriting: 0, cover: 0, audio: 0, topic: 0 },
        enabled_material_counts: { video: 1, copywriting: 0, cover: 0, audio: 0, topic: 0 },
      },
      generation_error_msg: null,
      generation_failed_at: null,
      pool_state: 'out_pool',
      active_pool_item_id: null,
      active_pool_version_id: null,
      active_pool_aligned: false,
      updated_at: '2026-04-16T08:00:00Z',
    },
    {
      id: 104,
      creative_no: 'CR-000104',
      title: 'Winter lookbook',
      status: 'REWORK_REQUIRED',
      current_version_id: null,
      subject_product_id: null,
      subject_product_name_snapshot: null,
      main_copywriting_text: null,
      target_duration_seconds: null,
      input_items: [],
      input_orchestration: {
        profile_id: null,
        orchestration_hash: 'orchestration-104',
        item_count: 0,
        enabled_item_count: 0,
        material_counts: { video: 0, copywriting: 0, cover: 0, audio: 0, topic: 0 },
        enabled_material_counts: { video: 0, copywriting: 0, cover: 0, audio: 0, topic: 0 },
      },
      generation_error_msg: null,
      generation_failed_at: null,
      pool_state: 'out_pool',
      active_pool_item_id: null,
      active_pool_version_id: null,
      active_pool_aligned: false,
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
  subject_product_id: 301,
  subject_product_name_snapshot: 'Classic Hoodie',
  main_copywriting_text: '轻盈春装，上身即走。',
  target_duration_seconds: 30,
  input_items: [
    {
      material_type: 'video',
      material_id: 11,
      role: '主镜头',
      sequence: 1,
      instance_no: 1,
      enabled: true,
    },
  ],
  input_orchestration: {
    profile_id: 1,
    orchestration_hash: 'orchestration-101',
    item_count: 1,
    enabled_item_count: 1,
    material_counts: { video: 1, copywriting: 0, cover: 0, audio: 0, topic: 0 },
    enabled_material_counts: { video: 1, copywriting: 0, cover: 0, audio: 0, topic: 0 },
  },
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

function hasRecentFailure(item: (typeof creativeListPayload.items)[number]) {
  return Boolean(item.generation_error_msg || item.status === 'FAILED' || item.generation_failed_at)
}

function getAttentionScore(item: (typeof creativeListPayload.items)[number]) {
  let score = 0

  if (hasRecentFailure(item)) {
    score += 400
  }

  if (item.status === 'REWORK_REQUIRED') {
    score += 300
  }

  if (item.status === 'WAITING_REVIEW') {
    score += 200
  }

  if (item.pool_state === 'version_mismatch') {
    score += 100
  }

  return score
}

function getCreativeListResponse(url: URL) {
  const keyword = url.searchParams.get('keyword')?.trim().toLowerCase()
  const status = url.searchParams.get('status')
  const poolState = url.searchParams.get('pool_state')
  const sort = url.searchParams.get('sort') ?? 'updated_desc'
  const recentFailuresOnly = url.searchParams.get('recent_failures_only') === 'true'
  const skip = Number.parseInt(url.searchParams.get('skip') ?? '0', 10)
  const limit = Number.parseInt(url.searchParams.get('limit') ?? `${creativeListPayload.items.length}`, 10)

  let filtered = creativeListPayload.items.filter((item) => {
    if (keyword) {
      const haystack = `${item.title ?? ''} ${item.creative_no}`.toLowerCase()
      if (!haystack.includes(keyword)) {
        return false
      }
    }

    if (status && item.status !== status) {
      return false
    }

    if (poolState && item.pool_state !== poolState) {
      return false
    }

    if (recentFailuresOnly && !hasRecentFailure(item)) {
      return false
    }

    return true
  })

  filtered = [...filtered].sort((left, right) => {
    const updatedAtDelta = Date.parse(right.updated_at) - Date.parse(left.updated_at)
    const failedAtDelta =
      Date.parse(right.generation_failed_at ?? right.updated_at) - Date.parse(left.generation_failed_at ?? left.updated_at)

    switch (sort) {
      case 'updated_asc':
        return -updatedAtDelta
      case 'attention_desc':
        if (getAttentionScore(right) !== getAttentionScore(left)) {
          return getAttentionScore(right) - getAttentionScore(left)
        }
        return updatedAtDelta
      case 'failed_desc':
        if (hasRecentFailure(right) !== hasRecentFailure(left)) {
          return Number(hasRecentFailure(right)) - Number(hasRecentFailure(left))
        }
        if (hasRecentFailure(right) && hasRecentFailure(left) && failedAtDelta !== 0) {
          return failedAtDelta
        }
        return updatedAtDelta
      case 'updated_desc':
      default:
        return updatedAtDelta
    }
  })

  return {
    total: filtered.length,
    items: filtered.slice(skip, skip + limit),
    summary: creativeListPayload.summary,
  }
}

async function mockCreativeApis(page: Page) {
  let creativeDetailState = JSON.parse(JSON.stringify(creativeDetailPayload)) as typeof creativeDetailPayload

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
    const url = new URL(route.request().url())
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(getCreativeListResponse(url)),
    })
  })

  await page.route('**/api/creatives/101', async (route) => {
    if (route.request().method() === 'PATCH') {
      const payload = route.request().postDataJSON() as Record<string, unknown>
      creativeDetailState = {
        ...creativeDetailState,
        title: payload.title === undefined ? creativeDetailState.title : String(payload.title ?? ''),
        subject_product_id:
          payload.subject_product_id === undefined ? creativeDetailState.subject_product_id : Number(payload.subject_product_id ?? 0) || null,
        subject_product_name_snapshot:
          payload.subject_product_name_snapshot === undefined
            ? creativeDetailState.subject_product_name_snapshot
            : (payload.subject_product_name_snapshot as string | null),
        main_copywriting_text:
          payload.main_copywriting_text === undefined
            ? creativeDetailState.main_copywriting_text
            : (payload.main_copywriting_text as string | null),
        target_duration_seconds:
          payload.target_duration_seconds === undefined
            ? creativeDetailState.target_duration_seconds
            : (payload.target_duration_seconds as number | null),
        input_items: Array.isArray(payload.input_items) ? payload.input_items as typeof creativeDetailPayload.input_items : creativeDetailState.input_items,
        updated_at: '2026-04-18T08:00:00Z',
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(creativeDetailState),
      })
      return
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(creativeDetailState),
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
      body: JSON.stringify({
        total: 1,
        items: [
          {
            id: 1,
            name: 'Default Profile',
            composition_mode: 'none',
            is_default: true,
          },
        ],
      }),
    })
  })

  await page.route('**/api/products?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 2,
        items: [
          { id: 301, name: 'Classic Hoodie', parse_status: 'ready', created_at: '2026-04-16T10:00:00Z', updated_at: '2026-04-16T10:00:00Z' },
          { id: 302, name: 'Runner Pro', parse_status: 'ready', created_at: '2026-04-16T10:00:00Z', updated_at: '2026-04-16T10:00:00Z' },
        ],
      }),
    })
  })

  await page.route('**/api/videos?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 3,
        items: [
          { id: 11, name: '开箱主镜头' },
          { id: 12, name: '细节转场素材' },
          { id: 13, name: '上身展示镜头' },
        ],
      }),
    })
  })

  await page.route('**/api/copywritings?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 2,
        items: [
          { id: 21, name: '卖点短句 A' },
          { id: 22, name: '卖点短句 B' },
        ],
      }),
    })
  })

  await page.route('**/api/covers?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 31, name: '封面首图' }]),
    })
  })

  await page.route('**/api/audios?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 41, name: '节奏音轨' }]),
    })
  })

  await page.route('**/api/topics?**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 2,
        items: [
          { id: 51, name: '#春日穿搭' },
          { id: 52, name: '#轻运动' },
        ],
      }),
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
    await page.goto(`/#/creative/workbench`)

    await expect(page.locator('body')).toContainText('集中处理作品创建、创作 brief、素材编排、审核与 AIClip 主流程')
    await expect(page.locator('body')).not.toContainText('兼容入口：新建任务')
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-open-diagnostics')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-scheduler-mode')).toHaveCount(0)
    await expect(page.getByTestId('creative-workbench-effective-mode')).toHaveCount(0)
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).toContainText('Classic Hoodie')
    await expect(page.locator('body')).toContainText('30 秒')
    await expect(page.locator('body')).toContainText('1 个编排项')
    await expect(page.locator('body')).toContainText('Summer sale teaser')
    await expect(page.getByTestId('creative-workbench-pool-state-101')).toContainText('已入发布池')
    await expect(page.getByTestId('creative-workbench-pool-state-102')).toContainText('版本未对齐')
    await expect(page.getByTestId('creative-workbench-open-review-101')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-ai-clip-101')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-preset-waiting_review')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-sort-select')).toBeVisible()
  })

  test('saves creative brief and input_items without legacy list write fields', async ({ page }) => {
    let updatePayload: Record<string, unknown> | undefined
    let detailState = JSON.parse(JSON.stringify(creativeDetailPayload)) as typeof creativeDetailPayload

    await page.unroute('**/api/creatives/101')
    await page.route('**/api/creatives/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        updatePayload = route.request().postDataJSON() as Record<string, unknown>
        detailState = {
          ...detailState,
          ...updatePayload,
          updated_at: '2026-04-18T08:00:00Z',
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(detailState),
        })
        return
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(detailState),
      })
    })

    await page.goto(`/#/creative/101`)

    await expect(page.locator('body')).toContainText('Default Profile')
    await expect(page.locator('body')).not.toContainText('Snapshot Hash')
    await expect(page.locator('body')).toContainText('创作 brief 与素材编排')
    await expect(page.getByTestId('creative-detail-product-snapshot')).toHaveValue('Classic Hoodie')
    await page.getByTestId('creative-detail-product-snapshot').fill('Runner Pro')
    await page.getByTestId('creative-detail-main-copywriting').fill('主推轻盈舒适与全天候穿着体验。')
    await page.getByLabel('目标时长（秒）').fill('45')
    await page.getByTestId('creative-detail-save-authoring').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      profile_id: 1,
      subject_product_name_snapshot: 'Runner Pro',
      main_copywriting_text: '主推轻盈舒适与全天候穿着体验。',
      target_duration_seconds: 45,
      input_items: [
        { material_type: 'video', material_id: 11, sequence: 1 },
      ],
    })
    expect(updatePayload).not.toHaveProperty('video_ids')
    expect(updatePayload).not.toHaveProperty('copywriting_ids')
    expect(updatePayload).not.toHaveProperty('cover_ids')
    expect(updatePayload).not.toHaveProperty('audio_ids')
    expect(updatePayload).not.toHaveProperty('topic_ids')
    await expect(page.locator('body')).toContainText('45 秒')
  })

  test('opens diagnostics through an explicit secondary entry', async ({ page }) => {
    await page.goto(`/#/creative/workbench`)

    await page.getByTestId('creative-workbench-open-diagnostics').click()

    await expect(page).toHaveURL(/diagnostics=runtime/)
    await expect(page.getByTestId('creative-workbench-diagnostics-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-effective-mode')).toContainText('Task')
    await expect(page.getByTestId('creative-workbench-runtime-status')).toContainText('空闲')

    await page.locator('.ant-drawer-close').click()
    await expect(page).not.toHaveURL(/diagnostics=runtime/)
    await expect(page.getByTestId('creative-workbench-diagnostics-drawer')).toHaveCount(0)
  })

  test('shows an explicit service-side retrieval notice for the workbench', async ({ page }) => {
    await page.goto(`/#/creative/workbench`)

    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    const guardrail = page.getByTestId('creative-workbench-server-search')

    await expect(guardrail).toBeVisible({ timeout: 10000 })
    await expect(guardrail).toContainText('已升级为服务端检索')
    await expect(guardrail).toContainText('不再受前端最近 200 条窗口限制')
    await expect(guardrail).toContainText('当前总量为 4 条')
  })

  test('supports search and filtering before entering detail', async ({ page }) => {
    await page.goto(`/#/creative/workbench`)

    await page.getByTestId('creative-workbench-search-input').fill('Spring')
    await page.getByRole('button', { name: '应用筛选' }).click()

    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')

    await page.getByTestId('creative-workbench-open-detail-101').click()

    await page.waitForURL(/#\/creative\/101\?returnTo=/)
    await expect(page.getByTestId('creative-open-advanced-diagnostics')).toBeVisible()
    await expect(page.getByTestId('creative-task-diagnostics-card')).toHaveCount(0)
    await expect(page.getByTestId('creative-publish-diagnostics')).toHaveCount(0)

    await page.getByTestId('creative-open-advanced-diagnostics').click()
    await expect(page).toHaveURL(/diagnostics=advanced/)
    await expect(page.getByTestId('creative-detail-diagnostics-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-task-diagnostics-card')).toBeVisible()
    await expect(page.getByTestId('creative-publish-diagnostics')).toBeVisible()

    await page.getByTestId('creative-open-task-diagnostics').click()
    await page.waitForURL(/#\/task\/901\?returnTo=/)
    await expect(page.getByTestId('task-detail-page')).toBeVisible()
    await expect(page.getByTestId('task-detail-back-to-list')).toBeVisible()
  })

  test('persists applied workbench state after refresh', async ({ page }) => {
    await page.goto(`/#/creative/workbench`)

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
      `/#/creative/workbench?keyword=Spring&status=WAITING_REVIEW&poolState=in_pool&sort=updated_desc&page=1&pageSize=10`,
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
    await page.goto(`/#/creative/workbench`)

    await page.getByTestId('creative-workbench-preset-recent_failures').click()

    await expect(page).toHaveURL(/preset=recent_failures/)
    await expect(page).toHaveURL(/sort=failed_desc/)
    await expect(page.locator('body')).toContainText('Summer sale teaser')
    await expect(page.locator('body')).not.toContainText('Spring campaign')
    await expectWorkbenchOrder(page, [102])
  })

  test('supports explicit workbench sort views', async ({ page }) => {
    await page.goto(`/#/creative/workbench`)

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

    await page.goto(`/#/creative/workbench`)

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

    await page.goto(`/#/creative/101`)

    await expect(page.getByTestId('creative-detail-error')).toBeVisible()
    await expect(page.locator('body')).toContainText('作品详情暂时无法加载')
  })
})
