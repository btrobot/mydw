import { expect, test } from '@playwright/test'

import { BASE_URL, mockCreativeReviewApis } from '../utils/creativeReviewMocks'

test.describe('Creative review drawer', () => {
  test.beforeEach(async ({ page }) => {
    await mockCreativeReviewApis(page)
  })

  test('supports approve flow on current version', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/101`)

    await page.getByTestId('creative-open-review').click()
    const drawer = page.getByRole('dialog', { name: '作品审核' })
    await expect(drawer).toBeVisible()

    await drawer.getByRole('textbox', { name: '审核说明' }).fill('视觉与文案均符合要求')
    await drawer.getByRole('button', { name: '提交审核' }).click()

    await expect(drawer).toBeHidden()
    await expect(page.getByTestId('creative-review-summary')).toContainText('通过')
    await expect(page.getByTestId('creative-review-summary')).toContainText('V2')
  })

  test('supports rework and reject flows', async ({ page }) => {
    await page.goto(`${BASE_URL}/#/creative/101`)

    await page.getByTestId('creative-open-review').click()
    let drawer = page.getByRole('dialog', { name: '作品审核' })

    await drawer.getByText('返工', { exact: true }).click()
    await drawer.getByRole('combobox', { name: '返工类型' }).click()
    await page.getByText('镜头返工', { exact: true }).click()
    await drawer.getByRole('textbox', { name: '审核说明' }).fill('镜头节奏需要继续调整')
    await drawer.getByRole('button', { name: '提交审核' }).click()

    await expect(page.getByTestId('creative-review-summary')).toContainText('返工')
    await expect(page.getByTestId('creative-review-summary')).toContainText('SHOT_REWORK')

    await page.getByTestId('creative-open-review').click()
    drawer = page.getByRole('dialog', { name: '作品审核' })
    await drawer.getByText('驳回', { exact: true }).click()
    await drawer.getByRole('textbox', { name: '审核说明' }).fill('不符合当前投放要求')
    await drawer.getByRole('button', { name: '提交审核' }).click()

    await expect(page.getByTestId('creative-review-summary')).toContainText('驳回')
    await expect(page.getByTestId('creative-review-summary')).toContainText('不符合当前投放要求')
  })
})
