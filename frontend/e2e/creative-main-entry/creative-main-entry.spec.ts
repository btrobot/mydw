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

test.describe('Creative main entry cutover', () => {
  test('redirects active sessions from root to workbench and keeps dashboard reachable', async ({ page }) => {
    await mockCreativeReviewApis(page, createCreativeReviewState())
    await mockDashboardRuntimeApis(page)

    await page.goto(`${BASE_URL}/#/`)
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()

    await page.getByTestId('creative-workbench-open-dashboard').click()
    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
  })

  test('redirects grace sessions from login to restricted workbench and still allows dashboard', async ({ page }) => {
    await mockWorkbenchLandingApis(page, { authState: 'authenticated_grace' })
    await mockDashboardRuntimeApis(page)

    await page.goto(`${BASE_URL}/#/login`)
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()

    await page.goto(`${BASE_URL}/#/dashboard`)
    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
  })
})
