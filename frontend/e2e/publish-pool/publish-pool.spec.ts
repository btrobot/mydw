import { expect, test } from '@playwright/test'

import {
  BASE_URL,
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'

test.describe('Phase C publish pool visibility', () => {
  test('workbench can filter pool candidates and detail keeps pool history in advanced diagnostics', async ({ page }) => {
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
          created_at: '2026-04-16T09:00:00Z',
          updated_at: '2026-04-17T09:00:00Z',
          creative_current_version_id: state.detail.current_version_id,
        },
      ],
    })

    await page.goto(`${BASE_URL}/#/creative/workbench`)

    await page.getByTestId('creative-workbench-open-diagnostics').click()
    await expect(page.getByTestId('creative-workbench-effective-mode')).toContainText('Pool')
    await page.locator('.ant-drawer-close').click()
    await expect(page.getByTestId('creative-workbench-diagnostics-drawer')).toHaveCount(0)
    await expect(page.locator('body')).toContainText('CR-000101')
    await expect(page.getByTestId('creative-workbench-pool-state-101')).toContainText('#202')

    await page.getByTestId('creative-workbench-open-detail-101').click()
    await page.waitForURL(/#\/creative\/101\?returnTo=/)

    await page.getByTestId('creative-open-advanced-diagnostics').click()
    await expect(page.getByTestId('creative-detail-diagnostics-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-publish-pool-card')).toContainText('Pool #501')
    await expect(page.getByTestId('creative-publish-pool-card')).toContainText('版本已对齐')
  })
})
