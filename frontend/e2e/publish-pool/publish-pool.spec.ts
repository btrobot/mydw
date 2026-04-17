import { expect, test } from '@playwright/test'

import {
  BASE_URL,
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'

test.describe('Phase C publish pool visibility', () => {
  test('workbench can filter pool candidates and detail projects current pool state', async ({ page }) => {
    const state = createCreativeReviewState()
    state.detail.status = 'APPROVED'

    await mockCreativeReviewApis(page, state, {
      scheduleConfig: {
        publish_scheduler_mode: 'pool',
      },
      publishStatus: {
        status: 'running',
        scheduler_mode: 'pool',
        effective_scheduler_mode: 'pool',
        total_pending: 1,
      },
      activePoolItems: [
        {
          id: 501,
          creative_item_id: state.detail.id,
          creative_version_id: state.detail.current_version_id,
          status: 'active',
          creative_no: state.detail.creative_no,
          creative_title: state.detail.title,
          creative_status: state.detail.status,
          creative_current_version_id: state.detail.current_version_id,
          created_at: '2026-04-17T07:30:00Z',
          updated_at: '2026-04-17T07:30:00Z',
        },
      ],
    })

    await page.goto(`${BASE_URL}/#/creative/workbench`)

    await expect(page.getByTestId('creative-workbench-effective-mode')).toContainText('Pool mode')
    await page.getByTestId('creative-workbench-pool-filter').getByText('In pool', { exact: true }).click()
    await expect(page.locator('body')).toContainText('CR-000101')
    await expect(page.getByTestId('creative-workbench-pool-state-101')).toContainText('Pool version #202')
    await expect(page.getByRole('button', { name: /publish/i })).toHaveCount(0)

    await page.getByTestId('creative-workbench-open-detail-101').click()
    await page.waitForURL('**/#/creative/101')

    await expect(page.getByTestId('creative-publish-diagnostics')).toContainText('Pool Item ID')
    await expect(page.getByTestId('creative-publish-pool-card')).toContainText('Pool #501')
  })
})
