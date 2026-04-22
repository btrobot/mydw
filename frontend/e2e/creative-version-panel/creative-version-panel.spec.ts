import { expect, test } from '@playwright/test'

import { mockCreativeReviewApis } from '../utils/creativeReviewMocks'

test.describe('Creative version panel', () => {
  test.beforeEach(async ({ page }) => {
    await mockCreativeReviewApis(page)
  })

  test('shows version history, current marker, and stale old approval', async ({ page }) => {
    await page.goto(`/#/creative/101`)

    await expect(page.getByTestId('creative-version-panel')).toBeVisible()
    await expect(page.getByTestId('creative-version-semantics')).toContainText('作品定义 → 版本结果 → 审核结论')
    await expect(page.getByTestId('creative-version-item-202')).toContainText('当前生效版本结果')
    await expect(page.getByTestId('creative-version-item-201')).toContainText('历史审核结论')
    await expect(page.getByTestId('creative-version-item-201')).toContainText('旧版本已通过')
    await expect(page.getByTestId('creative-review-summary')).toContainText('当前版本结果待审核')
  })

  test('after reviewing current version, old approval stays historical only', async ({ page }) => {
    await page.goto(`/#/creative/101`)

    await page.getByTestId('creative-open-review').click()
    const drawer = page.getByTestId('creative-check-drawer')
    await drawer.locator('textarea').fill('新版本确认通过')
    await drawer.getByTestId('creative-review-submit').click()

    await expect(page.getByTestId('creative-version-item-202')).toContainText('当前有效结论')
    await expect(page.getByTestId('creative-version-item-201')).toContainText('历史审核结论')
    await expect(page.getByTestId('creative-review-summary')).toContainText('新版本确认通过')
    await expect(page.getByTestId('creative-review-summary')).toContainText('V2')
  })

  test('task link remains available as diagnostic entry', async ({ page }) => {
    await page.goto(`/#/creative/101`)
    await page.getByTestId('creative-open-advanced-diagnostics').click()
    await expect(page.getByTestId('creative-detail-diagnostics-drawer')).toBeVisible()
    await page.getByTestId('creative-open-task-diagnostics').click()
    await page.waitForURL('**/#/task/901?returnTo=*')
    await expect(page.getByTestId('task-detail-page')).toBeVisible()
  })
})
