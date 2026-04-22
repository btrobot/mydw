import { expect, test } from '@playwright/test'

import {
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

    await page.goto(`/#/`)
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()

    await page.getByTestId('creative-workbench-open-dashboard').click()
    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
  })

  test('redirects grace sessions from login to restricted workbench and still allows dashboard', async ({ page }) => {
    await mockWorkbenchLandingApis(page, { authState: 'authenticated_grace' })
    await mockDashboardRuntimeApis(page)

    await page.goto(`/#/login`)
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.getByTestId('auth-grace-banner')).toContainText('当前处于宽限模式')
    await expect(page.getByTestId('auth-grace-banner')).toContainText('当前授权服务暂不可用，你仍可查看已有内容，但受保护操作会受到限制。')
    await expect(page.getByTestId('auth-session-status-tag')).toHaveText('宽限模式')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()

    await page.goto(`/#/dashboard`)
    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('auth-grace-banner')).toBeVisible()
    await expect(page.getByTestId('auth-grace-banner')).toContainText('当前处于宽限模式')
    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
  })
})
