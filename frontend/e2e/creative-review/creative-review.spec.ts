import { expect, test } from '@playwright/test'

import {
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'

test.describe('Creative review drawer', () => {
  let reviewState: ReturnType<typeof createCreativeReviewState>

  test.beforeEach(async ({ page }) => {
    reviewState = createCreativeReviewState()
    await mockCreativeReviewApis(page, reviewState)
  })

  test('supports approve flow on current version', async ({ page }) => {
    await page.goto(`/#/creative/101`)

    await expect(page.getByTestId('creative-current-version-semantics')).toContainText('并沉淀 adopted truth')
    await expect(page.getByTestId('creative-current-package-freeze')).toContainText('PackageRecord #302')
    await expect(page.getByTestId('creative-current-package-freeze')).toContainText('冻结商品名')
    await expect(page.getByTestId('creative-current-package-freeze')).toContainText('Classic Hoodie 春季轻运动版')
    await expect(page.getByTestId('creative-open-advanced-diagnostics')).toBeVisible()
    await expect(page.getByTestId('creative-publish-diagnostics')).toHaveCount(0)

    await page.getByTestId('creative-open-review').click()
    const drawer = page.getByTestId('creative-check-drawer')
    await expect(drawer).toBeVisible()

    await drawer.locator('textarea').fill('视觉与文案均符合要求')
    await drawer.getByTestId('creative-review-submit').click()

    await expect(drawer).toBeHidden()
    await expect(page.getByTestId('creative-review-summary-semantics')).toContainText('审核结论只判断当前版本结果是否可继续进入发布承接')
    await expect(page.getByTestId('creative-review-summary')).toContainText('通过')
    await expect(page.getByTestId('creative-review-summary')).toContainText('V2')
  })

  test('supports rework and reject flows', async ({ page }) => {
    await page.goto(`/#/creative/101`)

    await page.getByTestId('creative-open-review').click()
    let drawer = page.getByTestId('creative-check-drawer')

    await drawer.locator('.ant-radio-group label').nth(1).click()
    await drawer.getByTestId('creative-rework-type').click()
    await page.locator('.ant-select-dropdown .ant-select-item-option').nth(2).click()
    await drawer.locator('textarea').fill('镜头节奏需要继续调整')
    await drawer.getByTestId('creative-review-submit').click()

    await expect(page.getByTestId('creative-review-summary')).toContainText('返工')
    await expect(page.getByTestId('creative-review-summary')).toContainText('镜头返工')

    await page.getByTestId('creative-open-review').click()
    drawer = page.getByTestId('creative-check-drawer')
    await drawer.locator('.ant-radio-group label').nth(2).click()
    await drawer.locator('textarea').fill('不符合当前投放要求')
    await drawer.getByTestId('creative-review-submit').click()

    await expect(page.getByTestId('creative-review-summary')).toContainText('驳回')
    await expect(page.getByTestId('creative-review-summary')).toContainText('不符合当前投放要求')
  })

  test('requires rework type and trims review note before submit', async ({ page }) => {
    await page.goto(`/#/creative/101`)

    await page.getByTestId('creative-open-review').click()
    const drawer = page.getByTestId('creative-check-drawer')
    await drawer.locator('.ant-radio-group label').nth(1).click()
    await drawer.getByTestId('creative-review-submit').click()

    await expect(drawer).toBeVisible()
    await expect(drawer).toContainText('请选择具体返工类型')
    await expect(page.getByTestId('creative-review-summary')).toContainText('当前版本结果待审核')

    await drawer.getByTestId('creative-rework-type').click()
    await page.locator('.ant-select-dropdown .ant-select-item-option').nth(0).click()
    await drawer.locator('textarea').fill('  文案卖点需要更明确  ')
    await drawer.getByTestId('creative-review-submit').click()

    await expect(drawer).toBeHidden()
    expect(reviewState.detail.review_summary.current_check?.note).toBe('文案卖点需要更明确')
    await expect(page.getByTestId('creative-review-summary')).toContainText('文案卖点需要更明确')
  })

  test('resets draft review fields after cancel and reopen', async ({ page }) => {
    await page.goto(`/#/creative/101`)

    await page.getByTestId('creative-open-review').click()
    let drawer = page.getByTestId('creative-check-drawer')
    await drawer.locator('.ant-radio-group label').nth(1).click()
    await expect(drawer.getByTestId('creative-rework-type')).toBeVisible()
    await drawer.locator('textarea').fill('这次先不提交')
    await page.getByTestId('creative-review-cancel').click()

    await expect(drawer).toBeHidden()

    await page.getByTestId('creative-open-review').click()
    drawer = page.getByTestId('creative-check-drawer')
    await expect(drawer).toBeVisible()
    await expect(drawer.getByTestId('creative-rework-type')).toHaveCount(0)
    await expect(drawer.locator('textarea')).toHaveValue('')
    await expect(page.getByTestId('creative-review-summary')).toContainText('当前版本结果待审核')
  })
})
