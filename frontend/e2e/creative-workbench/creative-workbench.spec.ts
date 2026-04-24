import { expect, test, type Page } from '@playwright/test'

type CreativeListRequestSnapshot = {
  keyword: string | null
  status: string | null
  poolState: string | null
  sort: string | null
  recentFailuresOnly: string | null
  skip: string | null
  limit: string | null
}

const gotoHashRoute = async (page: Page, path: string): Promise<void> => {
  const baseUrl = process.env.E2E_BASE_URL || `http://127.0.0.1:${process.env.E2E_WEB_PORT || '4174'}`
  await page.goto(new URL(path, baseUrl).toString())
}

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
    selected_video_count: 4,
    selected_audio_count: 1,
    candidate_video_count: 3,
    candidate_audio_count: 1,
    candidate_cover_count: 1,
    definition_ready_count: 2,
    composition_ready_count: 2,
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
      current_product_name: 'Classic Hoodie',
      current_cover_thumb: null,
      current_copy_excerpt: '春季轻运动风。',
      product_name_mode: 'follow_primary_product',
      current_cover_asset_type: null,
      current_cover_asset_id: null,
      cover_mode: 'manual',
      current_copywriting_id: null,
      current_copywriting_text: '春季轻运动风。',
      copywriting_mode: 'manual',
      main_copywriting_text: '??????????',
      target_duration_seconds: 30,
      selected_video_count: 1,
      selected_audio_count: 0,
      candidate_video_count: 1,
      candidate_audio_count: 0,
      candidate_cover_count: 1,
      definition_ready: false,
      composition_ready: true,
      missing_required_fields: ['current_cover'],
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
      current_product_name: 'Runner Pro',
      current_cover_thumb: null,
      current_copy_excerpt: '夏日大促预热。',
      product_name_mode: 'manual',
      current_cover_asset_type: 'cover',
      current_cover_asset_id: 502,
      cover_mode: 'manual',
      current_copywriting_id: null,
      current_copywriting_text: '夏日大促预热。',
      copywriting_mode: 'manual',
      main_copywriting_text: '??????????',
      target_duration_seconds: 45,
      selected_video_count: 2,
      selected_audio_count: 1,
      candidate_video_count: 1,
      candidate_audio_count: 1,
      candidate_cover_count: 0,
      definition_ready: true,
      composition_ready: true,
      missing_required_fields: [],
      input_items: [
        { material_type: 'video', material_id: 12, sequence: 1, instance_no: 1, enabled: true },
        { material_type: 'video', material_id: 12, sequence: 2, instance_no: 2, enabled: true },
        { material_type: 'audio', material_id: 41, sequence: 3, instance_no: 1, enabled: true },
      ],
      input_orchestration: {
        profile_id: 1,
        orchestration_hash: 'orchestration-102',
        item_count: 3,
        enabled_item_count: 3,
        material_counts: { video: 2, copywriting: 0, cover: 0, audio: 1, topic: 0 },
        enabled_material_counts: { video: 2, copywriting: 0, cover: 0, audio: 1, topic: 0 },
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
      current_product_name: 'Trail Jacket',
      current_cover_thumb: null,
      current_copy_excerpt: '秋日氛围感故事。',
      product_name_mode: 'manual',
      current_cover_asset_type: null,
      current_cover_asset_id: null,
      cover_mode: 'manual',
      current_copywriting_id: null,
      current_copywriting_text: '秋日氛围感故事。',
      copywriting_mode: 'manual',
      main_copywriting_text: '?????????????',
      target_duration_seconds: 25,
      selected_video_count: 1,
      selected_audio_count: 0,
      candidate_video_count: 1,
      candidate_audio_count: 0,
      candidate_cover_count: 0,
      definition_ready: false,
      composition_ready: false,
      missing_required_fields: ['current_cover', 'input_profile'],
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
      current_product_name: null,
      current_cover_thumb: null,
      current_copy_excerpt: null,
      product_name_mode: 'manual',
      current_cover_asset_type: null,
      current_cover_asset_id: null,
      cover_mode: 'manual',
      current_copywriting_id: null,
      current_copywriting_text: null,
      copywriting_mode: 'manual',
      main_copywriting_text: null,
      target_duration_seconds: null,
      selected_video_count: 0,
      selected_audio_count: 0,
      candidate_video_count: 0,
      candidate_audio_count: 0,
      candidate_cover_count: 0,
      definition_ready: false,
      composition_ready: false,
      missing_required_fields: ['current_product_name', 'current_cover', 'current_copywriting', 'selected_video', 'input_profile'],
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
  current_product_name: 'Classic Hoodie',
  product_name_mode: 'follow_primary_product',
  current_cover_asset_type: null,
  current_cover_asset_id: null,
  cover_mode: 'manual',
  current_copywriting_id: null,
  current_copywriting_text: 'Lightweight spring styling.',
  copywriting_mode: 'manual',
  main_copywriting_text: '轻盈春装，上身即走。',
  target_duration_seconds: 30,
  candidate_items: [],
  input_items: [
    {
      material_type: 'video',
      material_id: 11,
      role: '主镜头',
      sequence: 1,
      instance_no: 1,
      enabled: true,
    },
    {
      material_type: 'copywriting',
      material_id: 21,
      role: '口播参考',
      sequence: 2,
      instance_no: 1,
      enabled: true,
    },
    {
      material_type: 'audio',
      material_id: 41,
      role: '配乐',
      sequence: 3,
      instance_no: 1,
      enabled: true,
    },
    {
      material_type: 'cover',
      material_id: 31,
      role: '封面参考',
      sequence: 4,
      instance_no: 1,
      enabled: true,
    },
    {
      material_type: 'topic',
      material_id: 51,
      role: '话题参考',
      sequence: 5,
      instance_no: 1,
      enabled: true,
    },
  ],
  input_orchestration: {
    profile_id: 1,
    orchestration_hash: 'orchestration-101',
    item_count: 5,
    enabled_item_count: 5,
    material_counts: { video: 1, copywriting: 1, cover: 1, audio: 1, topic: 1 },
    enabled_material_counts: { video: 1, copywriting: 1, cover: 1, audio: 1, topic: 1 },
  },
  current_selection: {
    product_name: {
      state: 'defined',
      value_text: 'Classic Hoodie',
      source_label: '跟随主题商品',
    },
    cover: {
      state: 'missing',
      source_label: '待从商品区或自由素材区选择封面',
    },
    copywriting: {
      state: 'defined',
      value_text: 'Lightweight spring styling.',
      source_label: '手工定义',
      detached: true,
    },
    audio: {
      state: 'defined',
      asset_type: 'audio',
      asset_id: 41,
      asset_name: 'Studio BGM 01',
      source_label: '当前入选音频',
    },
    videos: [
      {
        state: 'defined',
        asset_type: 'video',
        asset_id: 11,
        asset_name: 'Model Walkthrough',
        asset_excerpt: '主镜头',
        source_label: '当前入选视频',
        sequence: 1,
        instance_no: 1,
      },
    ],
  },
  product_zone: {
    primary_product: {
      id: 301,
      name: 'Classic Hoodie',
      link_id: 1,
      source_mode: 'import_bootstrap',
      is_primary: true,
      enabled: true,
      cover_count: 1,
      video_count: 2,
      copywriting_count: 1,
    },
    linked_products: [
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
    product_name_candidate: {
      product_id: 301,
      product_name: 'Classic Hoodie',
      is_selected: true,
      is_detached: false,
    },
    cover_candidates: [
      {
        candidate_type: 'cover',
        asset_id: 31,
        asset_name: '封面首图',
        source_kind: 'product_derived',
        source_product_id: 301,
        source_product_name: 'Classic Hoodie',
        is_selected: false,
        is_current_value: false,
      },
    ],
    video_candidates: [
      {
        candidate_type: 'video',
        asset_id: 11,
        asset_name: 'Model Walkthrough',
        source_kind: 'product_derived',
        source_product_id: 301,
        source_product_name: 'Classic Hoodie',
        is_selected: true,
        is_current_value: false,
      },
    ],
    copywriting_candidates: [
      {
        candidate_type: 'copywriting',
        asset_id: 21,
        asset_name: '卖点短句 A',
        asset_excerpt: '轻盈春装，上身即走。',
        source_kind: 'product_derived',
        source_product_id: 301,
        source_product_name: 'Classic Hoodie',
        is_selected: false,
        is_current_value: false,
      },
    ],
  },
  free_material_zone: {
    cover_candidates: [
      {
        candidate_type: 'cover',
        asset_id: 32,
        asset_name: '街拍封面',
        source_kind: 'manual_upload',
        is_selected: false,
        is_current_value: false,
      },
    ],
    video_candidates: [
      {
        candidate_type: 'video',
        asset_id: 12,
        asset_name: 'Street Cut',
        source_kind: 'material_library',
        is_selected: false,
        is_current_value: false,
      },
    ],
    audio_candidates: [
      {
        candidate_type: 'audio',
        asset_id: 41,
        asset_name: 'Studio BGM 01',
        source_kind: 'material_library',
        is_selected: true,
        is_current_value: false,
      },
    ],
    copywriting_candidates: [
      {
        candidate_type: 'copywriting',
        asset_id: 22,
        asset_name: '卖点短句 B',
        asset_excerpt: 'Copy Variant B',
        source_kind: 'llm_generated',
        is_selected: false,
        is_current_value: false,
      },
    ],
  },
  readiness: {
    state: 'result_pending_confirm',
    missing_fields: [],
    can_compose: false,
    next_action_hint: '当前已有结果，先确认是否沿用当前版本。',
  },
  page_mode: 'result_pending_confirm',
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

function createEditableCreativeDetailState() {
  return {
    ...JSON.parse(JSON.stringify(creativeDetailPayload)),
    status: 'READY_TO_COMPOSE',
    current_version_id: null,
    current_version: null,
    versions: [],
    review_summary: {
      current_version_id: null,
      current_check: null,
      total_checks: 0,
    },
    linked_task_ids: [],
    readiness: {
      state: 'ready',
      missing_fields: [],
      can_compose: true,
      next_action_hint: '当前定义已齐，可以直接提交生成。',
    },
    page_mode: 'definition',
    eligibility_status: 'READY_TO_COMPOSE',
    eligibility_reasons: [],
  } as typeof creativeDetailPayload & Record<string, unknown>
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

  await page.route('**/api/copywritings**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: 2,
        items: [
          { id: 21, name: '卖点短句 A', content: 'Copy Variant A' },
          { id: 22, name: '卖点短句 B', content: 'Copy Variant B' },
        ],
      }),
    })
  })

  await page.route('**/api/covers**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 31, name: '封面首图' }]),
    })
  })

  await page.route('**/api/audios**', async (route) => {
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

async function dragByTestId(page: Page, sourceTestId: string, targetTestId: string) {
  const dataTransfer = await page.evaluateHandle(() => new DataTransfer())
  await page.getByTestId(sourceTestId).dispatchEvent('dragstart', { dataTransfer })
  await page.getByTestId(targetTestId).dispatchEvent('dragover', { dataTransfer })
  await page.getByTestId(targetTestId).dispatchEvent('drop', { dataTransfer })
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

async function captureCreativeListRequests(page: Page) {
  const requests: CreativeListRequestSnapshot[] = []

  await page.unroute('**/api/creatives?**')
  await page.route('**/api/creatives?**', async (route) => {
    const url = new URL(route.request().url())
    requests.push({
      keyword: url.searchParams.get('keyword'),
      status: url.searchParams.get('status'),
      poolState: url.searchParams.get('pool_state'),
      sort: url.searchParams.get('sort'),
      recentFailuresOnly: url.searchParams.get('recent_failures_only'),
      skip: url.searchParams.get('skip'),
      limit: url.searchParams.get('limit'),
    })
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(getCreativeListResponse(url)),
    })
  })

  return requests
}

async function expectLatestCreativeRequest(
  requests: CreativeListRequestSnapshot[],
  expected: Partial<CreativeListRequestSnapshot>,
) {
  const expectedKeys = Object.keys(expected) as Array<keyof CreativeListRequestSnapshot>

  await expect.poll(() => {
    const latest = requests.at(-1)
    return Object.fromEntries(
      expectedKeys.map((key) => [key, latest?.[key] ?? null]),
    )
  }).toEqual(expected)
}

async function expectWorkbenchOrder(page: Page, creativeIds: number[]) {
  const actions = page.locator('[data-testid^="creative-workbench-open-detail-"]')
  await expect(actions).toHaveCount(creativeIds.length)

  for (const [index, creativeId] of creativeIds.entries()) {
    await expect(actions.nth(index)).toHaveAttribute('data-testid', `creative-workbench-open-detail-${creativeId}`)
  }
}

async function goToWorkbenchPage(page: Page, nextPage: number) {
  const nextPageButton = page.locator(`.ant-pagination-item-${nextPage}`)
  await expect(nextPageButton).toBeVisible()
  await nextPageButton.click()
}

test.describe('Creative workbench baseline', () => {
  test.beforeEach(async ({ page }) => {
    await mockCreativeApis(page)
  })

  test('shows the table-first workbench with business-first actions', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

    await expect(page.locator('body')).toContainText('集中处理作品创建、创作 brief、素材编排、审核与 AIClip 主流程')
    await expect(page.locator('body')).not.toContainText('兼容入口：新建任务')
    await expect(page.getByTestId('creative-workbench-publish-summary')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-open-diagnostics')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-summary-selected-video-count')).toContainText('4')
    await expect(page.getByTestId('creative-workbench-summary-composition-ready-count')).toContainText('2')
    await expect(page.getByTestId('creative-workbench-scheduler-mode')).toHaveCount(0)
    await expect(page.getByTestId('creative-workbench-effective-mode')).toHaveCount(0)
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).toContainText('Classic Hoodie')
    await expect(page.locator('body')).toContainText('30 秒')
    await expect(page.locator('body')).toContainText('入选视频 1')
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

    await gotoHashRoute(page, `/#/creative/101`)

    await expect(page.getByTestId('creative-detail-legacy-editor')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('[data-testid^="creative-detail-input-item-type-"]')).toHaveCount(2)
    await expect(page.getByTestId('creative-detail-product-snapshot')).toHaveValue('Classic Hoodie')
    await page.getByTestId('creative-detail-product-snapshot').fill('Runner Pro')
    await page.getByTestId('creative-detail-main-copywriting').fill('主推轻盈舒适与全天候穿着体验。')
    await page.getByLabel('目标时长（秒）').fill('45')
    await page.getByTestId('creative-detail-save-authoring').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      profile_id: 1,
      subject_product_id: 301,
      product_links: [
        { product_id: 301, sort_order: 1, is_primary: true },
      ],
      subject_product_name_snapshot: 'Runner Pro',
      main_copywriting_text: '主推轻盈舒适与全天候穿着体验。',
      target_duration_seconds: 45,
      candidate_items: [],
      input_items: [
        { material_type: 'video', material_id: 11, sequence: 1 },
        { material_type: 'audio', material_id: 41, sequence: 2 },
      ],
    })
    expect(updatePayload).not.toHaveProperty('video_ids')
    expect(updatePayload).not.toHaveProperty('copywriting_ids')
    expect(updatePayload).not.toHaveProperty('cover_ids')
    expect(updatePayload).not.toHaveProperty('audio_ids')
    expect(updatePayload).not.toHaveProperty('topic_ids')
    await expect(page.locator('body')).toContainText('45 秒')
  })

  test('renders projection-driven creative detail shell before legacy editor', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/101`)

    await expect(page.getByTestId('creative-detail-legacy-editor')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('creative-detail-shell-hero')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('creative-detail-shell-hero')).toContainText('结果待确认')
    await expect(page.getByTestId('creative-detail-shell-hero')).toContainText('当前模式：结果确认')
    await expect(page.getByTestId('creative-detail-hero-primary-review')).toBeVisible()
    await expect(page.getByTestId('creative-detail-mode-notice')).toContainText('当前已有结果待确认')
    await expect(page.getByTestId('creative-detail-current-selection')).toContainText('当前真正会进入生成的内容')
    await expect(page.getByTestId('creative-detail-current-selection')).toContainText('Classic Hoodie')
    await expect(page.getByTestId('creative-detail-product-zone')).toContainText('Classic Hoodie')
    await expect(page.getByTestId('creative-detail-free-material-zone')).toContainText('Studio BGM 01')
    await expect(page.getByTestId('creative-detail-legacy-editor')).toBeVisible({ timeout: 10000 })
  })

  test('switches hero summary and primary CTA back to authoring semantics when detail is editable', async ({ page }) => {
    const authoringState = createEditableCreativeDetailState()

    await page.unroute('**/api/creatives/101')
    await page.route('**/api/creatives/101', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(authoringState),
      })
    })

    await gotoHashRoute(page, `/#/creative/101`)

    await expect(page.getByTestId('creative-detail-shell-hero')).toContainText('readiness 摘要')
    await expect(page.getByTestId('creative-detail-shell-hero')).toContainText('当前模式：定义作品')
    await expect(page.getByTestId('creative-detail-hero-submit')).toBeVisible()
    await expect(page.getByTestId('creative-detail-mode-notice')).toHaveCount(0)
  })

  test('updates current selection from product and free-material zone actions before save', async ({ page }) => {
    let updatePayload: Record<string, unknown> | undefined
    let detailState = createEditableCreativeDetailState()

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

    await gotoHashRoute(page, `/#/creative/101`)

    await page.getByTestId('creative-product-zone-cover-apply-31').click()
    await page.getByTestId('creative-free-zone-copywriting-apply-22').click()
    await page.getByTestId('creative-free-zone-video-toggle-12').click()

    await expect(page.getByTestId('creative-detail-current-selection')).toContainText('封面首图')
    await expect(page.getByTestId('creative-detail-current-selection')).toContainText('Copy Variant B')
    await expect(page.getByTestId('creative-detail-current-selection')).toContainText('视频集合（2）')

    await page.getByTestId('creative-detail-hero-save').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      current_cover_asset_type: 'cover',
      current_cover_asset_id: 31,
      cover_mode: 'manual',
      current_copywriting_id: 22,
      current_copywriting_text: 'Copy Variant B',
      copywriting_mode: 'manual',
      input_items: [
        { material_type: 'video', material_id: 11, sequence: 1 },
        { material_type: 'audio', material_id: 41, sequence: 2 },
        { material_type: 'video', material_id: 12, sequence: 3 },
      ],
    })
  })

  test('supports in-zone editing and clearing inside the current selection section', async ({ page }) => {
    let updatePayload: Record<string, unknown> | undefined
    let detailState = createEditableCreativeDetailState()

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

    await gotoHashRoute(page, `/#/creative/101`)

    await page.getByTestId('creative-current-selection-product-name-input').fill('Spring Hoodie Pro')
    await page.getByTestId('creative-current-selection-copywriting-input').fill('改成当前主推文案。')
    await page.getByTestId('creative-current-selection-clear-audio').click()
    await page.getByTestId('creative-current-selection-remove-video-11').click()

    await expect(page.getByTestId('creative-detail-current-selection')).toContainText('Spring Hoodie Pro')
    await expect(page.getByTestId('creative-detail-current-selection')).toContainText('改成当前主推文案。')
    await expect(page.getByText('当前还没有入选视频。')).toBeVisible()

    await page.getByTestId('creative-detail-hero-save').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      current_product_name: 'Spring Hoodie Pro',
      product_name_mode: 'manual',
      current_copywriting_id: null,
      current_copywriting_text: '改成当前主推文案。',
      copywriting_mode: 'manual',
      input_items: [],
    })
  })

  test('supports in-zone video ordering and role editing inside current selection', async ({ page }) => {
    let updatePayload: Record<string, unknown> | undefined
    let detailState = createEditableCreativeDetailState()

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

    await gotoHashRoute(page, `/#/creative/101`)

    await page.getByTestId('creative-free-zone-video-toggle-12').click()
    await page.getByTestId('creative-current-selection-video-role-input-11-0').fill('开场镜头')
    await page.getByTestId('creative-current-selection-video-role-input-12-1').fill('结尾 CTA')
    await page.getByTestId('creative-current-selection-move-video-up-12-1').click()

    await expect(page.getByTestId('creative-current-selection-video-role-input-12-0')).toHaveValue('结尾 CTA')
    await expect(page.getByTestId('creative-current-selection-video-role-input-11-1')).toHaveValue('开场镜头')

    await page.getByTestId('creative-detail-hero-save').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      input_items: [
        { material_type: 'video', material_id: 12, role: '结尾 CTA', sequence: 1 },
        { material_type: 'audio', material_id: 41, role: '配乐', sequence: 2 },
        { material_type: 'video', material_id: 11, role: '开场镜头', sequence: 3 },
      ],
    })
  })

  test('supports in-zone video trim and slot duration editing inside current selection', async ({ page }) => {
    let updatePayload: Record<string, unknown> | undefined
    let detailState = createEditableCreativeDetailState()

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

    await gotoHashRoute(page, `/#/creative/101`)

    await page.getByTestId('creative-current-selection-video-slot-duration-11-0').locator('input').fill('12')
    await page.getByTestId('creative-current-selection-video-trim-in-11-0').locator('input').fill('1')
    await page.getByTestId('creative-current-selection-video-trim-out-11-0').locator('input').fill('9')

    await expect(page.getByTestId('creative-current-selection-video-slot-duration-11-0').locator('input')).toHaveValue('12')
    await expect(page.getByTestId('creative-current-selection-video-trim-in-11-0').locator('input')).toHaveValue('1')
    await expect(page.getByTestId('creative-current-selection-video-trim-out-11-0').locator('input')).toHaveValue('9')

    await page.getByTestId('creative-detail-hero-save').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      input_items: [
        {
          material_type: 'video',
          material_id: 11,
          role: '主镜头',
          sequence: 1,
          slot_duration_seconds: 12,
          trim_in: 1,
          trim_out: 9,
        },
        {
          material_type: 'audio',
          material_id: 41,
          role: '配乐',
          sequence: 2,
        },
      ],
    })
  })

  test('blocks save when current selection video timing is invalid', async ({ page }) => {
    let patchCount = 0
    let detailState = createEditableCreativeDetailState()

    await page.unroute('**/api/creatives/101')
    await page.route('**/api/creatives/101', async (route) => {
      if (route.request().method() === 'PATCH') {
        patchCount += 1
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

    await gotoHashRoute(page, `/#/creative/101`)

    await page.getByTestId('creative-current-selection-video-trim-in-11-0').locator('input').fill('10')
    await page.getByTestId('creative-current-selection-video-trim-out-11-0').locator('input').fill('5')

    await expect(page.getByTestId('creative-current-selection-video-warning-0')).toContainText('视频 #1 的裁切终点必须大于裁切起点')

    await page.getByTestId('creative-detail-hero-save').click()

    await expect(page.locator('body')).toContainText('视频 #1 的裁切终点必须大于裁切起点')
    expect(patchCount).toBe(0)
  })

  test('supports drag sorting inside current selection videos', async ({ page }) => {
    let updatePayload: Record<string, unknown> | undefined
    let detailState = createEditableCreativeDetailState()

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

    await gotoHashRoute(page, `/#/creative/101`)

    await page.getByTestId('creative-free-zone-video-toggle-12').click()
    await page.getByTestId('creative-current-selection-video-role-input-11-0').fill('开场镜头')
    await page.getByTestId('creative-current-selection-video-role-input-12-1').fill('结尾 CTA')

    await dragByTestId(
      page,
      'creative-current-selection-video-card-12-1',
      'creative-current-selection-video-card-11-0',
    )

    await expect(page.getByTestId('creative-current-selection-video-role-input-12-0')).toHaveValue('结尾 CTA')
    await expect(page.getByTestId('creative-current-selection-video-role-input-11-1')).toHaveValue('开场镜头')

    await page.getByTestId('creative-detail-hero-save').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      input_items: [
        { material_type: 'video', material_id: 12, role: '结尾 CTA', sequence: 1 },
        { material_type: 'audio', material_id: 41, role: '配乐', sequence: 2 },
        { material_type: 'video', material_id: 11, role: '开场镜头', sequence: 3 },
      ],
    })
  })

  test('filters full-carrier readback to video and audio operations only', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/101`)

    await expect(page.getByTestId('creative-detail-legacy-editor')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('[data-testid^="creative-detail-input-item-type-"]')).toHaveCount(2)

    await page.getByTestId('creative-detail-input-item-type-0').click()
    const visibleDropdown = page.locator('.ant-select-dropdown:visible').last()
    await expect(visibleDropdown).toContainText('视频素材')
    await expect(visibleDropdown).toContainText('音频素材')
    await expect(visibleDropdown).not.toContainText('文案素材')
    await expect(visibleDropdown).not.toContainText('封面素材')
    await expect(visibleDropdown).not.toContainText('话题素材')
    await page.keyboard.press('Escape')
  })

  test('persists candidate pool adoption separately from selected media state', async ({ page }) => {
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

    await gotoHashRoute(page, `/#/creative/101`)

    await page.getByTestId('creative-detail-add-candidate-cover').click()
    await chooseAntSelectOption(page, 'creative-detail-candidate-asset-cover-0', '封面首图')
    await page.getByTestId('creative-detail-adopt-candidate-cover-0').click()

    await page.getByTestId('creative-detail-add-candidate-copywriting').click()
    await chooseAntSelectOption(page, 'creative-detail-candidate-asset-copywriting-0', '卖点短句 B')
    await page.getByTestId('creative-detail-adopt-candidate-copywriting-0').click()

    await expect(page.getByTestId('creative-detail-adopt-candidate-cover-0')).toContainText('当前已采用')
    await expect(page.getByTestId('creative-detail-adopt-candidate-copywriting-0')).toContainText('当前已采用')

    await page.getByTestId('creative-detail-save-authoring').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    expect(updatePayload).toMatchObject({
      current_cover_asset_type: 'cover',
      current_cover_asset_id: 31,
      cover_mode: 'adopted_candidate',
      current_copywriting_id: 22,
      current_copywriting_text: 'Copy Variant B',
      copywriting_mode: 'adopted_candidate',
      main_copywriting_text: 'Copy Variant B',
      candidate_items: [
        {
          candidate_type: 'cover',
          asset_id: 31,
          source_kind: 'material_library',
          sort_order: 1,
          enabled: true,
          status: 'adopted',
        },
        {
          candidate_type: 'copywriting',
          asset_id: 22,
          source_kind: 'material_library',
          sort_order: 2,
          enabled: true,
          status: 'adopted',
        },
      ],
      input_items: [
        { material_type: 'video', material_id: 11, sequence: 1 },
        { material_type: 'audio', material_id: 41, sequence: 2 },
      ],
    })
  })

  test('writes taskId to detail URL only after submit composition succeeds', async ({ page }) => {
    let updatePayload: Record<string, unknown> | undefined
    let submitRequestCount = 0
    let urlBeforeSubmitFulfill: string | undefined
    let detailState: Record<string, unknown> = {
      ...JSON.parse(JSON.stringify(creativeDetailPayload)),
      eligibility_status: 'READY_TO_COMPOSE',
      eligibility_reasons: [],
    }

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

    await page.route('**/api/creatives/101/submit-composition', async (route) => {
      submitRequestCount += 1
      urlBeforeSubmitFulfill = page.url()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          creative_id: 101,
          task_id: 991,
          task_status: 'draft',
          creative_status: 'WAITING_REVIEW',
          current_version_id: 201,
          composition_mode: 'none',
          composition_job_id: null,
          composition_job_status: null,
          submission_action: 'created_ready_task',
          reused_existing_task: false,
          created_new_task: true,
        }),
      })
    })

    await gotoHashRoute(page, '/#/creative/101?returnTo=%2Fcreative%2Fworkbench%3Fpreset%3Dwaiting_review')

    await expect(page).not.toHaveURL(/taskId=991/)
    await page.getByTestId('creative-submit-composition').click()

    await expect.poll(() => updatePayload).toBeTruthy()
    await expect.poll(() => submitRequestCount).toBe(1)
    expect(urlBeforeSubmitFulfill).not.toContain('taskId=991')
    await expect(page).toHaveURL(/taskId=991/)
    await expect(page).toHaveURL(/returnTo=%2Fcreative%2Fworkbench%3Fpreset%3Dwaiting_review/)
  })

  test('opens diagnostics through an explicit secondary entry', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

    await page.getByTestId('creative-workbench-open-diagnostics').click()

    await expect(page).toHaveURL(/diagnostics=runtime/)
    await expect(page.getByTestId('creative-workbench-diagnostics-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-diagnostics-actions')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-effective-mode')).toContainText('Task')
    await expect(page.getByTestId('creative-workbench-runtime-status')).toContainText('空闲')

    await page.locator('.ant-drawer-close').click()
    await expect(page).not.toHaveURL(/diagnostics=runtime/)
    await expect(page.getByTestId('creative-workbench-diagnostics-drawer')).toHaveCount(0)
  })

  test('supports search and filtering before entering detail', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

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
    await expect(page.getByTestId('creative-detail-diagnostics-actions')).toBeVisible()
    await expect(page.getByTestId('creative-task-diagnostics-card')).toBeVisible()
    await expect(page.getByTestId('creative-publish-diagnostics')).toBeVisible()
    await expect(page.getByTestId('creative-detail-diagnostics-drawer').getByTestId('creative-submit-composition')).toHaveCount(0)

    await page.getByTestId('creative-open-task-diagnostics').click()
    await page.waitForURL(/#\/task\/901\?returnTo=/)
    await expect(page.getByTestId('task-detail-page')).toBeVisible()
    await expect(page.getByTestId('task-detail-back-to-list')).toBeVisible()
  })

  test('persists applied workbench state after refresh', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

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

  test('preserves sort and pagination state across refresh with matching skip/limit requests', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench?sort=attention_desc&page=2&pageSize=2`)

    await expect(page).toHaveURL(/sort=attention_desc/)
    await expect(page).toHaveURL(/page=2/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expectLatestCreativeRequest(requests, {
      sort: 'attention_desc',
      skip: '2',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [101, 103])

    await page.reload()

    await expect(page).toHaveURL(/sort=attention_desc/)
    await expect(page).toHaveURL(/page=2/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expectLatestCreativeRequest(requests, {
      sort: 'attention_desc',
      skip: '2',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [101, 103])
  })

  test('updates URL, request params, and visible rows when moving to the next page from the paginator', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench?sort=attention_desc&page=1&pageSize=2`)

    await expectLatestCreativeRequest(requests, {
      sort: 'attention_desc',
      skip: '0',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [102, 104])

    await goToWorkbenchPage(page, 2)

    await expect(page).toHaveURL(/sort=attention_desc/)
    await expect(page).toHaveURL(/page=2/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expectLatestCreativeRequest(requests, {
      sort: 'attention_desc',
      skip: '2',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [101, 103])
  })

  test('resets to page 1 and requests skip 0 when sort changes from page 2', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench?sort=attention_desc&page=2&pageSize=2`)

    await expectLatestCreativeRequest(requests, {
      sort: 'attention_desc',
      skip: '2',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [101, 103])

    await chooseWorkbenchSort(page, '最早更新优先')

    await expect(page).toHaveURL(/sort=updated_asc/)
    await expect(page).toHaveURL(/page=1/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expectLatestCreativeRequest(requests, {
      sort: 'updated_asc',
      skip: '0',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [103, 101])
  })

  test('returns to the filtered workbench state after entering detail', async ({ page }) => {
    await gotoHashRoute(
      page,
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

  test('returns to the original workbench URL after the detail -> task diagnostics round-trip', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench?sort=attention_desc&page=2&pageSize=2`)

    await expectWorkbenchOrder(page, [101, 103])

    await page.getByTestId('creative-workbench-open-detail-101').click()
    await page.waitForURL(/#\/creative\/101\?returnTo=/)

    await page.getByTestId('creative-open-advanced-diagnostics').click()
    await expect(page).toHaveURL(/diagnostics=advanced/)

    await page.getByTestId('creative-open-task-diagnostics').click()
    await page.waitForURL(/#\/task\/901\?returnTo=/)

    await page.getByTestId('task-detail-back-to-list').click()

    await page.waitForURL(/#\/creative\/workbench\?sort=attention_desc&page=2&pageSize=2$/)
    await expectWorkbenchOrder(page, [101, 103])
  })

  test('supports preset views for high-frequency queues', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

    await page.getByTestId('creative-workbench-preset-waiting_review').click()

    await expect(page).toHaveURL(/preset=waiting_review/)
    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/sort=updated_desc/)
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')
    await expect(page.locator('body')).not.toContainText('Winter lookbook')
    await expectWorkbenchOrder(page, [101])

    await page.getByTestId('creative-workbench-preset-needs_rework').click()

    await expect(page).toHaveURL(/preset=needs_rework/)
    await expect(page).toHaveURL(/status=REWORK_REQUIRED/)
    await expect(page).toHaveURL(/sort=updated_desc/)
    await expect(page.locator('body')).toContainText('Winter lookbook')
    await expect(page.locator('body')).not.toContainText('Spring campaign')
    await expect(page.locator('body')).not.toContainText('Summer sale teaser')
    await expectWorkbenchOrder(page, [104])

    await page.getByTestId('creative-workbench-preset-recent_failures').click()

    await expect(page).toHaveURL(/preset=recent_failures/)
    await expect(page).toHaveURL(/sort=failed_desc/)
    await expect(page.locator('body')).toContainText('Summer sale teaser')
    await expect(page.locator('body')).not.toContainText('Spring campaign')
    await expectWorkbenchOrder(page, [102])
  })

  test('maps the recent failures preset to recent_failures_only request semantics', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench`)

    await page.getByTestId('creative-workbench-preset-recent_failures').click()

    await expect(page).toHaveURL(/preset=recent_failures/)
    await expect(page).toHaveURL(/sort=failed_desc/)
    await expectLatestCreativeRequest(requests, {
      sort: 'failed_desc',
      recentFailuresOnly: 'true',
      skip: '0',
      limit: '10',
    })
    await expectWorkbenchOrder(page, [102])
  })

  test('preserves preset state when only pageSize differs in the canonical URL', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench?preset=waiting_review&status=WAITING_REVIEW&sort=updated_desc&page=1&pageSize=2`)

    await expect(page).toHaveURL(/preset=waiting_review/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expectLatestCreativeRequest(requests, {
      status: 'WAITING_REVIEW',
      sort: 'updated_desc',
      skip: '0',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [101])

    await page.reload()

    await expect(page).toHaveURL(/preset=waiting_review/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expectLatestCreativeRequest(requests, {
      status: 'WAITING_REVIEW',
      sort: 'updated_desc',
      skip: '0',
      limit: '2',
    })
    await expectWorkbenchOrder(page, [101])
  })

  test('clears preset when a manual sort makes the current preset incompatible', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

    await page.getByTestId('creative-workbench-preset-waiting_review').click()
    await expect(page).toHaveURL(/preset=waiting_review/)

    await chooseWorkbenchSort(page, '待处理优先')

    await expect(page).not.toHaveURL(/preset=waiting_review/)
    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/sort=attention_desc/)
    await expectWorkbenchOrder(page, [101])
  })

  test('keeps diagnostics as route chrome and does not rewrite business query state', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench?keyword=Spring&status=WAITING_REVIEW&poolState=in_pool&sort=updated_desc&page=1&pageSize=2`)

    await expectLatestCreativeRequest(requests, {
      keyword: 'Spring',
      status: 'WAITING_REVIEW',
      poolState: 'in_pool',
      sort: 'updated_desc',
      skip: '0',
      limit: '2',
    })
    const requestCount = requests.length

    await page.getByTestId('creative-workbench-open-diagnostics').click()

    await expect(page).toHaveURL(/keyword=Spring/)
    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/poolState=in_pool/)
    await expect(page).toHaveURL(/sort=updated_desc/)
    await expect(page).toHaveURL(/page=1/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expect(page).toHaveURL(/diagnostics=runtime/)
    await expect(page.getByTestId('creative-workbench-diagnostics-drawer')).toBeVisible()
    await expect.poll(() => requests.length).toBe(requestCount)

    await page.locator('.ant-drawer-close').click()

    await expect(page).toHaveURL(/keyword=Spring/)
    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/poolState=in_pool/)
    await expect(page).toHaveURL(/sort=updated_desc/)
    await expect(page).toHaveURL(/page=1/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expect(page).not.toHaveURL(/diagnostics=runtime/)
    await expect.poll(() => requests.length).toBe(requestCount)
  })

  test('keeps runtime diagnostics open when recommendation CTAs switch preset views', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench?sort=updated_desc&page=2&pageSize=2`)

    await expectLatestCreativeRequest(requests, {
      sort: 'updated_desc',
      skip: '2',
      limit: '2',
    })

    await page.getByTestId('creative-workbench-open-diagnostics').click()
    await expect(page).toHaveURL(/diagnostics=runtime/)
    await expect(page.getByTestId('creative-workbench-diagnostics-actions')).toBeVisible()

    await page.getByTestId('creative-workbench-diagnostics-action-recent-failures').click()

    await expect(page).toHaveURL(/preset=recent_failures/)
    await expect(page).toHaveURL(/sort=failed_desc/)
    await expect(page).toHaveURL(/page=1/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expect(page).toHaveURL(/diagnostics=runtime/)
    await expectLatestCreativeRequest(requests, {
      sort: 'failed_desc',
      recentFailuresOnly: 'true',
      skip: '0',
      limit: '2',
    })
    await expect(page.getByTestId('creative-workbench-effective-mode')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-runtime-status')).toBeVisible()

    await page.locator('.ant-drawer-close').click()

    await expect(page).toHaveURL(/preset=recent_failures/)
    await expect(page).toHaveURL(/sort=failed_desc/)
    await expect(page).not.toHaveURL(/diagnostics=runtime/)
  })

  test('does not promote unapplied draft filters when opening diagnostics or changing sort', async ({ page }) => {
    const requests = await captureCreativeListRequests(page)

    await gotoHashRoute(page, `/#/creative/workbench?status=WAITING_REVIEW&sort=updated_desc&page=1&pageSize=2`)

    await expectLatestCreativeRequest(requests, {
      status: 'WAITING_REVIEW',
      sort: 'updated_desc',
      skip: '0',
      limit: '2',
      keyword: null,
    })
    const initialRequestCount = requests.length

    await page.getByTestId('creative-workbench-search-input').fill('Winter')

    await expect(page).not.toHaveURL(/keyword=Winter/)
    await expect.poll(() => requests.length).toBe(initialRequestCount)

    await page.getByTestId('creative-workbench-open-diagnostics').click()

    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/sort=updated_desc/)
    await expect(page).toHaveURL(/pageSize=2/)
    await expect(page).not.toHaveURL(/keyword=Winter/)
    await expect.poll(() => requests.length).toBe(initialRequestCount)

    await page.locator('.ant-drawer-close').click()

    await chooseWorkbenchSort(page, '待处理优先')

    await expect(page).toHaveURL(/status=WAITING_REVIEW/)
    await expect(page).toHaveURL(/sort=attention_desc/)
    await expect(page).not.toHaveURL(/keyword=Winter/)
    await expectLatestCreativeRequest(requests, {
      status: 'WAITING_REVIEW',
      sort: 'attention_desc',
      skip: '0',
      limit: '2',
      keyword: null,
    })
    await expectWorkbenchOrder(page, [101])
  })

  test('restores the full list after cycling preset buttons back to all', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

    await page.getByTestId('creative-workbench-preset-waiting_review').click()
    await expectWorkbenchOrder(page, [101])

    await page.getByTestId('creative-workbench-preset-needs_rework').click()
    await expectWorkbenchOrder(page, [104])

    await page.getByTestId('creative-workbench-preset-recent_failures').click()
    await expectWorkbenchOrder(page, [102])

    await page.getByTestId('creative-workbench-preset-version_mismatch').click()
    await expectWorkbenchOrder(page, [102])

    await page.getByTestId('creative-workbench-preset-recent_failures').click()
    await expectWorkbenchOrder(page, [102])

    await page.getByTestId('creative-workbench-preset-needs_rework').click()
    await expectWorkbenchOrder(page, [104])

    await page.getByTestId('creative-workbench-preset-waiting_review').click()
    await expectWorkbenchOrder(page, [101])

    await page.getByTestId('creative-workbench-preset-all').click()

    await expect(page).toHaveURL(/preset=all/)
    await expect(page).not.toHaveURL(/status=/)
    await expect(page).not.toHaveURL(/poolState=/)
    await expectWorkbenchOrder(page, [102, 104, 101, 103])
    await expect(page.locator('body')).toContainText('Summer sale teaser')
    await expect(page.locator('body')).toContainText('Winter lookbook')
    await expect(page.locator('body')).toContainText('Spring campaign')
    await expect(page.locator('body')).toContainText('Autumn story board')
  })

  test('supports explicit workbench sort views', async ({ page }) => {
    await gotoHashRoute(page, `/#/creative/workbench`)

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

    await gotoHashRoute(page, `/#/creative/workbench`)

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

    await gotoHashRoute(page, `/#/creative/101`)

    await expect(page.getByTestId('creative-detail-error')).toBeVisible()
    await expect(page.locator('body')).toContainText('作品详情暂时无法加载')
  })
})
