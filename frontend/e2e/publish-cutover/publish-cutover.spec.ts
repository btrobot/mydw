import { expect, test } from '@playwright/test'

import {
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'

test.describe('Phase C cutover diagnostics', () => {
  test('detail keeps publish failures reachable from the advanced diagnostics area', async ({ page }) => {
    const state = createCreativeReviewState()
    state.detail.status = 'APPROVED'
    state.detail.generation_error_msg = 'publish pipeline timeout'
    state.detail.generation_failed_at = '2026-04-17T08:00:00Z'
    state.detail.linked_task_ids = [901, 902]

    await mockCreativeReviewApis(page, state, {
      scheduleConfig: {
        publish_scheduler_mode: 'pool',
        publish_pool_shadow_read: true,
      },
      publishStatus: {
        status: 'paused',
        current_task_id: 903,
        total_failed: 1,
        scheduler_mode: 'pool',
        effective_scheduler_mode: 'pool',
        publish_pool_shadow_read: true,
        scheduler_shadow_diff: {
          legacy_task_id: 901,
          pool_item_id: 502,
          pool_task_id: 903,
          differs: true,
          reasons: ['legacy_task_diff', 'pool_candidate_locked'],
        },
      },
      invalidatedPoolItems: [
        {
          id: 502,
          creative_item_id: state.detail.id,
          creative_version_id: state.detail.current_version_id,
          status: 'invalidated',
          invalidation_reason: 'publish_failed',
          invalidated_at: '2026-04-17T08:01:00Z',
          creative_no: state.detail.creative_no,
          creative_title: state.detail.title,
          creative_status: state.detail.status,
          creative_current_version_id: state.detail.current_version_id,
          created_at: '2026-04-17T07:30:00Z',
          updated_at: '2026-04-17T08:01:00Z',
        },
      ],
      taskDetails: {
        903: {
          id: 903,
          name: 'Pool publish task',
          status: 'failed',
          account_id: 1,
          account_name: 'Creative Task Account',
          profile_id: null,
          priority: 0,
          scheduled_time: null,
          final_video_path: null,
          upload_url: null,
          error_msg: 'publish_failed',
          created_at: '2026-04-17T08:00:00Z',
          updated_at: '2026-04-17T08:02:00Z',
          video_ids: [],
          copywriting_ids: [],
          cover_ids: [],
          audio_ids: [],
          topic_ids: [],
        },
      },
    })

    await page.goto(`/#/creative/101`)

    await expect(page.locator('body')).toContainText('publish pipeline timeout')

    await page.getByTestId('creative-open-advanced-diagnostics').click()
    await expect(page.getByTestId('creative-detail-diagnostics-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-publish-semantics')).toContainText('当前执行引擎能力尚未覆盖')
    await expect(page.getByTestId('creative-publish-diagnostics')).toContainText('Pool')
    await expect(page.getByTestId('creative-publish-pool-card')).toContainText('publish_failed')
    await expect(page.getByTestId('creative-shadow-diff')).toContainText('legacy_task_diff')
    await expect(page.getByTestId('creative-shadow-diff')).toContainText('pool_candidate_locked')

    await page.getByTestId('creative-open-task-903').click()
    await page.waitForURL('**/#/task/903?returnTo=*')
    await expect(page.getByTestId('task-detail-page')).toBeVisible()
  })
})

