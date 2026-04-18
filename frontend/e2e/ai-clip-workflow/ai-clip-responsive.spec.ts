import { expect, test } from '@playwright/test'

import {
  BASE_URL,
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'
import {
  mockDashboardRuntimeApis,
  mockWorkbenchLandingApis,
} from '../utils/workbenchEntryMocks'

test.describe('AIClip and shell responsive baseline', () => {
  test.use({ viewport: { width: 390, height: 844 } })

  test('dashboard remains usable in a narrow viewport', async ({ page }) => {
    await mockWorkbenchLandingApis(page)
    await mockDashboardRuntimeApis(page)

    await page.goto(`${BASE_URL}/#/`)
    await page.waitForURL('**/#/creative/workbench')

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/dashboard')

    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
    await expect(page.getByTestId('dashboard-open-workbench')).toBeVisible()
    await expect(page.getByTestId('dashboard-open-task-list')).toBeVisible()
  })

  test('AIClip drawer keeps primary workflow controls reachable on narrow screens', async ({ page }) => {
    await mockCreativeReviewApis(page, createCreativeReviewState())

    await page.route('**/api/ai/full-pipeline', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          output_path: 'D:/exports/mobile_ai_clip.mp4',
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/creative/101`)
    await page.getByTestId('creative-open-ai-clip').click()

    await expect(page.getByTestId('creative-ai-clip-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-ai-clip-run-pipeline')).toBeVisible()

    await page.getByTestId('creative-ai-clip-video-path').fill('D:/videos/source.mp4')
    await page.getByTestId('creative-ai-clip-run-pipeline').click()

    await expect(page.getByTestId('creative-ai-clip-output-path')).toHaveValue('D:/exports/mobile_ai_clip.mp4')
    await expect(page.getByTestId('creative-ai-clip-submit')).toBeVisible()
  })

  test('review drawer remains operable on narrow screens', async ({ page }) => {
    await mockCreativeReviewApis(page, createCreativeReviewState())

    await page.goto(`${BASE_URL}/#/creative/101`)
    await page.getByTestId('creative-open-review').click()

    await expect(page.getByTestId('creative-check-drawer')).toBeVisible()
    await expect(page.getByTestId('creative-review-submit')).toBeVisible()
  })
})
