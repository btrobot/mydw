import type { Page, Route } from '@playwright/test'

export const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:4173'

type ReviewConclusion = 'APPROVED' | 'REWORK_REQUIRED' | 'REJECTED'

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

interface CreativeVersion {
  id: number
  creative_item_id: number
  parent_version_id?: number | null
  version_no: number
  version_type: string
  title?: string | null
  package_record_id?: number | null
  is_current?: boolean
  latest_check?: CheckRecord | null
  created_at: string
  updated_at: string
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
      package_record_id?: number | null
      latest_check?: CheckRecord | null
    }
    versions: CreativeVersion[]
    review_summary: {
      current_version_id?: number | null
      current_check?: CheckRecord | null
      total_checks?: number
    }
    linked_task_ids: number[]
    generation_error_msg?: string | null
    generation_failed_at?: string | null
    updated_at: string
  }
  nextCheckId: number
}

function buildCheck(
  state: CreativeScenarioState,
  versionId: number,
  conclusion: ReviewConclusion,
  note?: string,
  reworkType?: string,
): CheckRecord {
  const now = new Date().toISOString()
  return {
    id: state.nextCheckId++,
    creative_item_id: state.detail.id,
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

function syncCurrentVersion(state: CreativeScenarioState) {
  const currentVersion = getVersion(state, state.detail.current_version_id)
  state.detail.current_version = {
    id: currentVersion.id,
    version_no: currentVersion.version_no,
    title: currentVersion.title ?? '',
    parent_version_id: currentVersion.parent_version_id ?? null,
    package_record_id: currentVersion.package_record_id ?? null,
    latest_check: currentVersion.latest_check ?? null,
  }
}

function applyReview(
  state: CreativeScenarioState,
  versionId: number,
  conclusion: ReviewConclusion,
  note?: string,
  reworkType?: string,
) {
  const version = getVersion(state, versionId)
  const check = buildCheck(state, versionId, conclusion, note, reworkType)
  version.latest_check = check
  state.detail.status = conclusion
  state.detail.review_summary = {
    current_version_id: versionId,
    current_check: check,
    total_checks: (state.detail.review_summary.total_checks ?? 0) + 1,
  }
  state.detail.updated_at = check.updated_at
  syncCurrentVersion(state)

  return {
    creative_id: state.detail.id,
    creative_status: state.detail.status,
    current_version_id: state.detail.current_version_id,
    check,
  }
}

export function createCreativeReviewState(): CreativeScenarioState {
  const approvedAt = '2026-04-16T09:00:00Z'

  return {
    nextCheckId: 9002,
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
        package_record_id: 302,
        latest_check: null,
      },
      versions: [
        {
          id: 202,
          creative_item_id: 101,
          parent_version_id: 201,
          version_no: 2,
          version_type: 'COMPOSITION',
          title: '二次修订版',
          package_record_id: 302,
          is_current: true,
          latest_check: null,
          created_at: '2026-04-17T07:00:00Z',
          updated_at: '2026-04-17T07:00:00Z',
        },
        {
          id: 201,
          creative_item_id: 101,
          parent_version_id: null,
          version_no: 1,
          version_type: 'COMPOSITION',
          title: '初版',
          package_record_id: 301,
          is_current: false,
          latest_check: {
            id: 9001,
            creative_item_id: 101,
            creative_version_id: 201,
            conclusion: 'APPROVED',
            rework_type: null,
            note: '旧版本已通过',
            created_at: approvedAt,
            updated_at: approvedAt,
          },
          created_at: '2026-04-16T08:00:00Z',
          updated_at: approvedAt,
        },
      ],
      review_summary: {
        current_version_id: undefined,
        current_check: null,
        total_checks: 1,
      },
      linked_task_ids: [901],
      updated_at: '2026-04-17T07:00:00Z',
    },
  }
}

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

export async function mockCreativeReviewApis(page: Page, state = createCreativeReviewState()) {
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
    await fulfillJson(route, {
      total: 1,
      items: [
        {
          id: state.detail.id,
          creative_no: state.detail.creative_no,
          title: state.detail.title,
          status: state.detail.status,
          current_version_id: state.detail.current_version_id,
          generation_error_msg: state.detail.generation_error_msg ?? null,
          generation_failed_at: state.detail.generation_failed_at ?? null,
          updated_at: state.detail.updated_at,
        },
      ],
    })
  })

  await page.route(`**/api/creatives/${state.detail.id}`, async (route) => {
    await fulfillJson(route, state.detail)
  })

  await page.route(`**/api/creative-reviews/${state.detail.id}/approve`, async (route) => {
    const payload = route.request().postDataJSON() as { version_id: number; note?: string }
    await fulfillJson(route, applyReview(state, payload.version_id, 'APPROVED', payload.note))
  })

  await page.route(`**/api/creative-reviews/${state.detail.id}/rework`, async (route) => {
    const payload = route.request().postDataJSON() as {
      version_id: number
      note?: string
      rework_type?: string
    }
    await fulfillJson(
      route,
      applyReview(
        state,
        payload.version_id,
        'REWORK_REQUIRED',
        payload.note,
        payload.rework_type,
      ),
    )
  })

  await page.route(`**/api/creative-reviews/${state.detail.id}/reject`, async (route) => {
    const payload = route.request().postDataJSON() as { version_id: number; note?: string }
    await fulfillJson(route, applyReview(state, payload.version_id, 'REJECTED', payload.note))
  })

  await page.route('**/api/accounts**', async (route) => {
    await fulfillJson(route, [
      {
        id: 1,
        account_id: 'creative-task-account',
        account_name: 'Creative Task Account',
        status: 'active',
      },
    ])
  })

  await page.route('**/api/profiles**', async (route) => {
    await fulfillJson(route, { total: 0, items: [] })
  })

  await page.route(`**/api/tasks/${state.detail.linked_task_ids[0]}/composition-status`, async (route) => {
    await fulfillJson(route, { detail: 'composition job not found' }, 404)
  })

  await page.route(`**/api/tasks/${state.detail.linked_task_ids[0]}`, async (route) => {
    await fulfillJson(route, {
      id: state.detail.linked_task_ids[0],
      name: '作品诊断任务',
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
    })
  })

  await page.route('**/api/tasks?**', async (route) => {
    await fulfillJson(route, { total: 0, items: [] })
  })

  return state
}
