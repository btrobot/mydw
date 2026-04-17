import { expect, test } from '@playwright/test'

import { BASE_URL, mockCreativeReviewApis } from '../utils/creativeReviewMocks'

test.describe('Creative version panel', () => {
  test.beforeEach(async ({ page }) => {
    await mockCreativeReviewApis(page)
  })

  test('shows version history, current marker, and stale old approval', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/101`)

    await expect(page.getByTestId('creative-version-panel')).toBeVisible()
    await expect(page.getByTestId('creative-version-item-202')).toContainText('当前生效版本')
    await expect(page.getByTestId('creative-version-item-201')).toContainText('历史结论')
    await expect(page.getByTestId('creative-version-item-201')).toContainText('旧版本已通过')
    await expect(page.getByTestId('creative-review-summary')).toContainText('当前版本还没有有效审核结论')
  })

  test('after reviewing current version, old approval stays historical only', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/101`)

    await page.getByTestId('creative-open-review').click()
    const drawer = page.getByRole('dialog', { name: '作品审核' })
    await drawer.getByRole('textbox', { name: '审核说明' }).fill('新版本确认通过')
    await drawer.getByRole('button', { name: '提交审核' }).click()

    await expect(page.getByTestId('creative-version-item-202')).toContainText('当前有效结论')
    await expect(page.getByTestId('creative-version-item-201')).toContainText('历史结论')
    await expect(page.getByTestId('creative-review-summary')).toContainText('新版本确认通过')
    await expect(page.getByTestId('creative-review-summary')).toContainText('V2')
  })

  test('task link remains available as diagnostic entry', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/101`)

    await page.getByRole('button', { name: '查看关联任务' }).click()
    await page.waitForURL('**/#/task/901')
    await expect(page.locator('body')).toContainText('任务详情 #901')
  })
})
