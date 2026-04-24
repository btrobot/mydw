import type { Page, Route } from '@playwright/test'

type ReviewConclusion = 'APPROVED' | 'REWORK_REQUIRED' | 'REJECTED'
type PublishPoolStatus = 'active' | 'invalidated'

interface CheckRecord {
  id: number
  creative_item_id: number
  creative_version_id: number
  conclusion: ReviewConclusion
  rework_type?: string | null
  note?: string | null
  created_at: string
  updated_at: string
}

interface PackageRecord {
  id: number
  creative_version_id: number
  package_status: string
  publish_profile_id?: number | null
  frozen_video_path?: string | null
  frozen_cover_path?: string | null
  frozen_duration_seconds?: number | null
  frozen_product_name?: string | null
  frozen_copywriting_text?: string | null
  manifest_json?: string | null
  created_at: string
  updated_at: string
}

interface CreativeVersion {
  id: number
  creative_item_id: number
  parent_version_id?: number | null
  version_no: number
  version_type: string
  title?: string | null
  actual_duration_seconds?: number | null
  final_video_path?: string | null
  final_product_name?: string | null
  final_copywriting_text?: string | null
  package_record_id?: number | null
  package_record?: PackageRecord | null
  is_current?: boolean
  latest_check?: CheckRecord | null
  created_at: string
  updated_at: string
}

interface PublishPoolItem {
  id: number
  creative_item_id: number
  creative_version_id: number
  status: PublishPoolStatus
  created_at: string
  updated_at: string
  invalidation_reason?: string | null
  invalidated_at?: string | null
  creative_no?: string | null
  creative_title?: string | null
  creative_status?: string | null
  creative_current_version_id?: number | null
}

interface CreativeScenarioState {
  detail: {
    id: number
    creative_no: string
    title: string
    status: 'WAITING_REVIEW' | 'APPROVED' | 'REWORK_REQUIRED' | 'REJECTED'
    current_version_id: number
    current_version: {
      id: number
      version_no: number
      title: string
      parent_version_id?: number | null
      actual_duration_seconds?: number | null
      final_video_path?: string | null
      final_product_name?: string | null
      final_copywriting_text?: string | null
      package_record_id?: number | null
      package_record?: PackageRecord | null
    }
    versions: CreativeVersion[]
    review_summary: {
      current_version_id?: number | null
      current_check?: CheckRecord | null
      total_checks?: number
    }
    linked_task_ids: number[]
    updated_at: string
    product_links?: Array<Record<string, unknown>>
    subject_product_id?: number | null
    subject_product_name_snapshot?: string | null
    main_copywriting_text?: string | null
    target_duration_seconds?: number | null
    input_items?: Array<Record<string, unknown>>
    input_orchestration?: Record<string, unknown>
    eligibility_status?: string
    eligibility_reasons?: string[]
    latest_task_summary?: Record<string, unknown> | null
    generation_error_msg?: string | null
    generation_failed_at?: string | null
  }
}

interface CreativeReviewMockOptions {
  publishStatus?: Record<string, unknown>
  scheduleConfig?: Record<string, unknown>
  activePoolItems?: PublishPoolItem[]
  invalidatedPoolItems?: PublishPoolItem[]
  taskDetails?: Record<number, Record<string, unknown>>
}

function createInputOrchestration(
  inputItems: Array<Record<string, unknown>>,
  profileId: number | null = 1,
  overrides: Record<string, unknown> = {},
) {
  const materialCounts = { video: 0, copywriting: 0, cover: 0, audio: 0, topic: 0 }
  const enabledMaterialCounts = { video: 0, copywriting: 0, cover: 0, audio: 0, topic: 0 }

  for (const item of inputItems) {
    const materialType = String(item.material_type ?? 'video') as keyof typeof materialCounts
    materialCounts[materialType] += 1
    if (item.enabled !== false) {
      enabledMaterialCounts[materialType] += 1
    }
  }

  return {
    profile_id: profileId,
    orchestration_hash: 'mock-review-orchestration',
    item_count: inputItems.length,
    enabled_item_count: inputItems.filter((item) => item.enabled !== false).length,
    material_counts: materialCounts,
    enabled_material_counts: enabledMaterialCounts,
    ...overrides,
  }
}

function createCreativeBriefFields(overrides: Record<string, unknown> = {}) {
  const inputItems = [
    {
      material_type: 'video',
      material_id: 11,
      sequence: 1,
      instance_no: 1,
      role: '主镜头',
      enabled: true,
    },
  ]
  return {
    product_links: [
      {
        id: 1,
        product_id: 301,
        product_name: 'Classic Hoodie',
        sort_order: 1,
        is_primary: true,
        enabled: true,
        source_mode: 'import_bootstrap',
      },
    ],
    subject_product_id: 301,
    subject_product_name_snapshot: 'Classic Hoodie',
    main_copywriting_text: '轻盈春装，上身即走。',
    target_duration_seconds: 30,
    input_items: inputItems,
    input_orchestration: createInputOrchestration(inputItems),
    eligibility_status: 'READY_TO_COMPOSE',
    eligibility_reasons: [],
    latest_task_summary: null,
    ...overrides,
  }
}

function buildCreativeListItem(
  detail: CreativeScenarioState['detail'],
  activePoolItems: PublishPoolItem[] = [],
) {
  const activePoolItem = activePoolItems.find((item) => item.creative_item_id === detail.id && item.status === 'active')
  const poolState = !activePoolItem
    ? 'out_pool'
    : activePoolItem.creative_version_id === detail.current_version_id
      ? 'in_pool'
      : 'version_mismatch'

  return {
    id: detail.id,
    creative_no: detail.creative_no,
    title: detail.title,
    status: detail.status,
    current_version_id: detail.current_version_id,
    subject_product_id: detail.subject_product_id ?? null,
    subject_product_name_snapshot: detail.subject_product_name_snapshot ?? null,
    main_copywriting_text: detail.main_copywriting_text ?? null,
    target_duration_seconds: detail.target_duration_seconds ?? null,
    input_items: detail.input_items ?? [],
    input_orchestration: detail.input_orchestration ?? createInputOrchestration(detail.input_items ?? []),
    generation_error_msg: detail.generation_error_msg ?? null,
    generation_failed_at: detail.generation_failed_at ?? null,
    pool_state: poolState,
    active_pool_item_id: activePoolItem?.id ?? null,
    active_pool_version_id: activePoolItem?.creative_version_id ?? null,
    active_pool_aligned: Boolean(activePoolItem && activePoolItem.creative_version_id === detail.current_version_id),
    eligibility_status: detail.eligibility_status ?? 'READY_TO_COMPOSE',
    eligibility_reasons: detail.eligibility_reasons ?? [],
    latest_task_summary: detail.latest_task_summary ?? null,
    updated_at: detail.updated_at,
  }
}

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({ json: body })
}

function buildCheck(
  creativeId: number,
  versionId: number,
  conclusion: ReviewConclusion,
  note?: string,
  reworkType?: string,
): CheckRecord {
  const now = new Date().toISOString()
  return {
    id: Math.floor(Math.random() * 10_000),
    creative_item_id: creativeId,
    creative_version_id: versionId,
    conclusion,
    rework_type: reworkType ?? null,
    note: note ?? null,
    created_at: now,
    updated_at: now,
  }
}

function getVersion(state: CreativeScenarioState, versionId: number): CreativeVersion {
  const version = state.detail.versions.find((item) => item.id === versionId)
  if (!version) {
    throw new Error(`Version ${versionId} not found in mock state`)
  }
  return version
}

function updateCurrentVersion(state: CreativeScenarioState, currentVersion: CreativeVersion) {
  state.detail.current_version = {
    id: currentVersion.id,
    version_no: currentVersion.version_no,
    title: currentVersion.title ?? '',
    parent_version_id: currentVersion.parent_version_id ?? null,
    actual_duration_seconds: currentVersion.actual_duration_seconds ?? null,
    final_video_path: currentVersion.final_video_path ?? null,
    final_product_name: currentVersion.final_product_name ?? null,
    final_copywriting_text: currentVersion.final_copywriting_text ?? null,
    package_record_id: currentVersion.package_record_id ?? null,
    package_record: currentVersion.package_record ?? null,
  }
  state.detail.current_version_id = currentVersion.id
}

function applyReview(
  state: CreativeScenarioState,
  versionId: number,
  conclusion: ReviewConclusion,
  note?: string,
  reworkType?: string,
) {
  const version = getVersion(state, versionId)
  const check = buildCheck(state.detail.id, versionId, conclusion, note, reworkType)

  version.latest_check = check
  state.detail.status = conclusion === 'APPROVED'
    ? 'APPROVED'
    : conclusion === 'REWORK_REQUIRED'
      ? 'REWORK_REQUIRED'
      : 'REJECTED'
  state.detail.review_summary = {
    current_version_id: versionId,
    current_check: check,
    total_checks: (state.detail.review_summary.total_checks ?? 0) + 1,
  }
  state.detail.updated_at = check.updated_at
  return { success: true, check }
}

function createTaskBody(taskId: number) {
  return {
    id: taskId,
    name: '作品诊断任务',
    status: 'draft',
    account_id: 1,
    account_name: 'Creative Task Account',
    profile_id: null,
    priority: 5,
    scheduled_time: null,
    final_video_path: null,
    upload_url: null,
    creative_item_id: 101,
    creative_version_id: 202,
    created_at: '2026-04-17T07:00:00Z',
    updated_at: '2026-04-17T07:00:00Z',
    video_ids: [],
    copywriting_ids: [],
    cover_ids: [],
    audio_ids: [],
    topic_ids: [],
  }
}

export function createCreativeReviewState(): CreativeScenarioState {
  const approvedAt = '2026-04-16T09:00:00Z'
  const currentPackageRecord = buildPackageRecord(302, 202)
  const historyPackageRecord = buildPackageRecord(301, 201, {
    frozen_video_path: '/publish/package-301.mp4',
    frozen_cover_path: '/publish/package-301.png',
    frozen_duration_seconds: 26,
    frozen_product_name: 'Classic Hoodie 首版',
    frozen_copywriting_text: '首发款上线，轻松出街。',
  })
  return {
    detail: {
      id: 101,
      creative_no: 'CR-000101',
      title: '春季作品样本',
      status: 'WAITING_REVIEW',
      current_version_id: 202,
      current_version: {
        id: 202,
        version_no: 2,
        title: '二次修订版',
        parent_version_id: 201,
        actual_duration_seconds: 28,
        final_video_path: '/creative/version-202.mp4',
        final_product_name: 'Classic Hoodie 春季轻运动版',
        final_copywriting_text: '轻盈上身，即刻出发。',
        package_record_id: 302,
        package_record: currentPackageRecord,
      },
      versions: [
        {
          id: 202,
          creative_item_id: 101,
          parent_version_id: 201,
          version_no: 2,
          version_type: 'COMPOSITION',
          title: '二次修订版',
          actual_duration_seconds: 28,
          final_video_path: '/creative/version-202.mp4',
          final_product_name: 'Classic Hoodie 春季轻运动版',
          final_copywriting_text: '轻盈上身，即刻出发。',
          package_record_id: 302,
          package_record: currentPackageRecord,
          is_current: true,
          latest_check: null,
          created_at: '2026-04-16T10:00:00Z',
          updated_at: '2026-04-17T08:00:00Z',
        },
        {
          id: 201,
          creative_item_id: 101,
          parent_version_id: null,
          version_no: 1,
          version_type: 'COMPOSITION',
          title: '初版',
          actual_duration_seconds: 26,
          final_video_path: '/creative/version-201.mp4',
          final_product_name: 'Classic Hoodie 首版',
          final_copywriting_text: '首发款上线，轻松出街。',
          package_record_id: 301,
          package_record: historyPackageRecord,
          is_current: false,
          latest_check: {
            id: 501,
            creative_item_id: 101,
            creative_version_id: 201,
            conclusion: 'APPROVED',
            rework_type: null,
            note: '旧版本已通过',
            created_at: approvedAt,
            updated_at: approvedAt,
          },
          created_at: '2026-04-15T08:00:00Z',
          updated_at: approvedAt,
        },
      ],
      review_summary: {
        current_version_id: null,
        current_check: null,
        total_checks: 1,
      },
      linked_task_ids: [901],
      updated_at: '2026-04-17T08:00:00Z',
      generation_error_msg: null,
      generation_failed_at: null,
      ...createCreativeBriefFields(),
    },
  }
}

function buildPackageRecord(
  id: number,
  creativeVersionId: number,
  overrides: Partial<PackageRecord> = {},
): PackageRecord {
  const createdAt = overrides.created_at ?? '2026-04-16T09:30:00Z'
  const updatedAt = overrides.updated_at ?? createdAt
  return {
    id,
    creative_version_id: creativeVersionId,
    package_status: 'ready',
    publish_profile_id: 88,
    frozen_video_path: `/publish/package-${id}.mp4`,
    frozen_cover_path: `/publish/package-${id}.png`,
    frozen_duration_seconds: 28,
    frozen_product_name: 'Classic Hoodie 春季轻运动版',
    frozen_copywriting_text: '春季轻装，轻盈上身，即刻出发。',
    manifest_json: null,
    created_at: createdAt,
    updated_at: updatedAt,
    ...overrides,
  }
}

function buildDefaultPublishStatus() {
  return {
    status: 'idle',
    current_task_id: null,
    total_pending: 0,
    total_success: 0,
    total_failed: 0,
    scheduler_mode: 'task',
    effective_scheduler_mode: 'task',
    publish_pool_shadow_read: false,
    publish_pool_kill_switch: false,
    scheduler_shadow_diff: null,
  }
}

function buildDefaultScheduleConfig() {
  return {
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
  }
}

function buildDefaultSystemConfig() {
  return {
    material_base_path: 'E:/mock-materials',
    creative_flow_mode: 'creative_first',
    creative_flow_shadow_compare: false,
  }
}

function filterPoolItems(items: PublishPoolItem[], url: URL) {
  const status = url.searchParams.get('status')
  const creativeId = url.searchParams.get('creative_id')

  return items.filter((item) => {
    if (status && item.status !== status) {
      return false
    }
    if (creativeId && item.creative_item_id !== Number.parseInt(creativeId, 10)) {
      return false
    }
    return true
  })
}

function paginate<T>(items: T[], url: URL) {
  const skip = Number.parseInt(url.searchParams.get('skip') ?? '0', 10)
  const limit = Number.parseInt(url.searchParams.get('limit') ?? `${items.length || 50}`, 10)
  return {
    total: items.length,
    items: items.slice(skip, skip + limit),
  }
}

export async function mockCreativeReviewApis(
  page: Page,
  state = createCreativeReviewState(),
  options: CreativeReviewMockOptions = {},
) {
  const scheduleConfig = { ...buildDefaultScheduleConfig(), ...options.scheduleConfig }
  const publishStatus = { ...buildDefaultPublishStatus(), ...options.publishStatus }
  const systemConfig = buildDefaultSystemConfig()
  const activePoolItems = options.activePoolItems ?? []
  const invalidatedPoolItems = options.invalidatedPoolItems ?? []

  await page.route('**/api/auth/session', async (route) => {
    await fulfillJson(route, {
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
    })
  })

  await page.route('**/api/creatives?**', async (route) => {
    const listItem = buildCreativeListItem(state.detail, activePoolItems)
    await fulfillJson(route, {
      total: 1,
      items: [listItem],
      summary: {
        all_count: 1,
        waiting_review_count: listItem.status === 'WAITING_REVIEW' ? 1 : 0,
        pending_input_count: listItem.status === 'PENDING_INPUT' ? 1 : 0,
        needs_rework_count: listItem.status === 'REWORK_REQUIRED' ? 1 : 0,
        recent_failures_count: listItem.generation_error_msg || listItem.generation_failed_at ? 1 : 0,
        active_pool_count: listItem.active_pool_item_id ? 1 : 0,
        aligned_pool_count: listItem.pool_state === 'in_pool' ? 1 : 0,
        version_mismatch_count: listItem.pool_state === 'version_mismatch' ? 1 : 0,
      },
    })
  })

  await page.route(`**/api/creatives/${state.detail.id}`, async (route) => {
    if (route.request().method() === 'PATCH') {
      const payload = route.request().postDataJSON() as Record<string, unknown>
      const nextInputItems = Array.isArray(payload.input_items)
        ? payload.input_items.map((item, index) => ({
          sequence: index + 1,
          instance_no: index + 1,
          enabled: true,
          ...(item as Record<string, unknown>),
        }))
        : (state.detail.input_items ?? [])
      const nextProfileId =
        payload.profile_id === undefined ? (state.detail.input_orchestration?.profile_id as number | null | undefined) : payload.profile_id as number | null
      const nextProductLinks = Array.isArray(payload.product_links)
        ? payload.product_links.map((item, index) => ({
          sort_order: index + 1,
          enabled: true,
          ...(item as Record<string, unknown>),
        }))
        : (state.detail.product_links ?? [])
      const primaryProductLink = nextProductLinks.find((item) => item.is_primary)

      state.detail = {
        ...state.detail,
        title: payload.title === undefined ? state.detail.title : String(payload.title ?? ''),
        product_links: nextProductLinks,
        subject_product_id:
          primaryProductLink?.product_id === undefined
            ? (payload.subject_product_id === undefined ? state.detail.subject_product_id ?? null : Number(payload.subject_product_id ?? 0) || null)
            : Number(primaryProductLink.product_id ?? 0) || null,
        subject_product_name_snapshot:
          payload.subject_product_name_snapshot === undefined
            ? state.detail.subject_product_name_snapshot ?? null
            : (payload.subject_product_name_snapshot as string | null),
        main_copywriting_text:
          payload.main_copywriting_text === undefined
            ? state.detail.main_copywriting_text ?? null
            : (payload.main_copywriting_text as string | null),
        target_duration_seconds:
          payload.target_duration_seconds === undefined
            ? state.detail.target_duration_seconds ?? null
            : (payload.target_duration_seconds as number | null),
        input_items: nextInputItems,
        input_orchestration: createInputOrchestration(nextInputItems, nextProfileId ?? null),
        updated_at: '2026-04-18T08:00:00Z',
      }

      await fulfillJson(route, state.detail)
      return
    }

    updateCurrentVersion(state, getVersion(state, state.detail.current_version_id))
    await fulfillJson(route, state.detail)
  })

  await page.route('**/api/publish/status**', async (route) => {
    await fulfillJson(route, publishStatus)
  })

  await page.route('**/api/system/config**', async (route) => {
    await fulfillJson(route, systemConfig)
  })

  await page.route('**/api/schedule-config**', async (route) => {
    await fulfillJson(route, scheduleConfig)
  })

  await page.route('**/api/creative-publish-pool**', async (route) => {
    const url = new URL(route.request().url())
    const merged = [...activePoolItems, ...invalidatedPoolItems]
    const filtered = filterPoolItems(merged, url)
    await fulfillJson(route, paginate(filtered, url))
  })

  await page.route(`**/api/creative-reviews/${state.detail.id}/approve`, async (route) => {
    const payload = route.request().postDataJSON() as { version_id: number; note?: string }
    await fulfillJson(route, applyReview(state, payload.version_id, 'APPROVED', payload.note))
  })

  await page.route(`**/api/creative-reviews/${state.detail.id}/rework`, async (route) => {
    const payload = route.request().postDataJSON() as { version_id: number; note?: string; rework_type?: string }
    await fulfillJson(route, applyReview(state, payload.version_id, 'REWORK_REQUIRED', payload.note, payload.rework_type))
  })

  await page.route(`**/api/creative-reviews/${state.detail.id}/reject`, async (route) => {
    const payload = route.request().postDataJSON() as { version_id: number; note?: string }
    await fulfillJson(route, applyReview(state, payload.version_id, 'REJECTED', payload.note))
  })

  await page.route('**/api/accounts**', async (route) => {
    await fulfillJson(route, [{ id: 1, account_id: 'creative-task-account', account_name: 'Creative Task Account', status: 'active' }])
  })

  await page.route('**/api/profiles**', async (route) => {
    await fulfillJson(route, {
      total: 1,
      items: [
        {
          id: 1,
          name: 'Default Profile',
          composition_mode: 'none',
          is_default: true,
        },
      ],
    })
  })

  await page.route('**/api/products?**', async (route) => {
    await fulfillJson(route, {
      total: 2,
      items: [
        { id: 301, name: 'Classic Hoodie', parse_status: 'ready', video_count: 1, copywriting_count: 1, cover_count: 0, topic_count: 0, created_at: '2026-04-17T08:00:00Z', updated_at: '2026-04-17T08:00:00Z' },
        { id: 302, name: 'Runner Pro', parse_status: 'ready', video_count: 2, copywriting_count: 1, cover_count: 1, topic_count: 1, created_at: '2026-04-17T08:00:00Z', updated_at: '2026-04-17T08:00:00Z' },
      ],
    })
  })

  await page.route('**/api/videos?**', async (route) => {
    await fulfillJson(route, {
      total: 2,
      items: [
        { id: 11, name: '开箱主镜头' },
        { id: 12, name: '细节转场素材' },
      ],
    })
  })

  await page.route('**/api/copywritings**', async (route) => {
    await fulfillJson(route, {
      total: 2,
      items: [
        { id: 21, name: '卖点短句 A', content: 'Copy Variant A' },
        { id: 22, name: '卖点短句 B', content: 'Copy Variant B' },
      ],
    })
  })

  await page.route('**/api/covers**', async (route) => {
    await fulfillJson(route, [
      { id: 31, name: '封面首图' },
    ])
  })

  await page.route('**/api/audios**', async (route) => {
    await fulfillJson(route, [
      { id: 41, name: '节奏音轨' },
    ])
  })

  await page.route('**/api/topics?**', async (route) => {
    await fulfillJson(route, {
      total: 2,
      items: [
        { id: 51, name: '#春日穿搭' },
        { id: 52, name: '#轻运动' },
      ],
    })
  })

  await page.route('**/api/tasks/*', async (route) => {
    const taskId = Number.parseInt(route.request().url().split('/').pop() ?? '0', 10)
    const taskBody = options.taskDetails?.[taskId] ?? createTaskBody(taskId)
    await fulfillJson(route, taskBody)
  })

  await page.route('**/api/tasks/*/composition-status', async (route) => {
    await route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'composition job not found' }),
    })
  })

  await page.route('**/api/tasks?**', async (route) => {
    const list = state.detail.linked_task_ids.map((taskId) => options.taskDetails?.[taskId] ?? createTaskBody(taskId))
    const url = new URL(route.request().url())
    await fulfillJson(route, paginate(list, url))
  })

  await page.route('**/api/compositions/*', async (route) => {
    await fulfillJson(route, { total: 0, items: [] })
  })

  return { state, publishStatus, scheduleConfig, systemConfig, activePoolItems, invalidatedPoolItems }
}
