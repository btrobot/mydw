import { expect, test, type Page } from '@playwright/test'

import {
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'
import {
  mockDashboardRuntimeApis,
  mockWorkbenchLandingApis,
} from '../utils/workbenchEntryMocks'

async function mockShellParityApis(page: Page) {
  await mockWorkbenchLandingApis(page)
  await mockDashboardRuntimeApis(page)

  await page.route('**/api/system/config**', async (route) => {
    await route.fulfill({
      json: {
        material_base_path: 'E:/mock-materials',
        creative_flow_mode: 'creative_first',
        creative_flow_shadow_compare: false,
      },
    })
  })

  await page.route('**/api/system/material-stats**', async (route) => {
    await route.fulfill({
      json: {
        videos: 0,
        copywritings: 0,
        covers: 0,
        audios: 0,
        topics: 0,
        products: 0,
        coverage_rate: 0,
      },
    })
  })

  await page.route('**/api/tasks?**', async (route) => {
    await route.fulfill({ json: { total: 0, items: [] } })
  })

  await page.route('**/api/accounts**', async (route) => {
    await route.fulfill({ json: [] })
  })

  await page.route('**/api/profiles**', async (route) => {
    await route.fulfill({ json: { total: 0, items: [] } })
  })
}

async function expectSelected(page: Page, testId: string) {
  const menuItem = page.getByTestId(testId).locator('xpath=ancestor::li[contains(@class, "ant-menu-item") or contains(@class, "ant-menu-submenu")]').first()
  await expect(menuItem).toHaveClass(/ant-menu-(item|submenu)-selected/)
}

async function expectMobileSiderCollapsed(page: Page) {
  const sider = page.getByTestId('app-shell-sider')
  if (await sider.count() === 0) return
  await expect(sider).toHaveClass(/ant-layout-sider-collapsed/)
}

async function expectMobileSiderExpanded(page: Page) {
  const sider = page.getByTestId('app-shell-sider')
  await expect(sider).toBeVisible()
  await expect(sider).not.toHaveClass(/ant-layout-sider-collapsed/)
}

test.describe('ADP shell parity gate', () => {
  test('preserves HashRouter menu navigation and auth header', async ({ page }) => {
    await mockShellParityApis(page)

    await page.goto('/#/creative/workbench')

    await expect(page.getByTestId('app-shell')).toBeVisible()
    await expect(page.getByTestId('app-shell-header')).toBeVisible()
    await expect(page.getByTestId('auth-session-status-tag')).toBeVisible()
    await expectSelected(page, 'app-shell-menu-creative-workbench')

    await page.getByTestId('app-shell-menu-dashboard').click()
    await page.waitForURL('**/#/dashboard')
    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
    await expectSelected(page, 'app-shell-menu-dashboard')

    await page.getByTestId('app-shell-menu-creative-workbench').click()
    await page.waitForURL('**/#/creative/workbench')
    await expect(page.getByTestId('creative-workbench-main-entry-banner')).toBeVisible()
    await expectSelected(page, 'app-shell-menu-creative-workbench')
  })

  test('keeps grouped menu labels as route entry points', async ({ page }) => {
    await mockShellParityApis(page)

    await page.goto('/#/creative/workbench')

    await page.getByTestId('app-shell-menu-task-group').click()
    await page.waitForURL('**/#/task/list**')
    await expectSelected(page, 'app-shell-menu-task-group')

    await page.getByTestId('app-shell-menu-material-group').click()
    await page.waitForURL('**/#/material')
    await expectSelected(page, 'app-shell-menu-material-group')
  })

  test('highlights Workbench for creative detail routes', async ({ page }) => {
    await mockCreativeReviewApis(page, createCreativeReviewState())

    await page.goto('/#/creative/101')

    await expect(page.getByTestId('app-shell')).toBeVisible()
    await expectSelected(page, 'app-shell-menu-creative-workbench')
  })

  test('collapses mobile navigation after selecting a route', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 800 })
    await mockShellParityApis(page)

    await page.goto('/#/creative/workbench')
    await expectMobileSiderCollapsed(page)

    await page.getByLabel('toggle-navigation').click()
    await expectMobileSiderExpanded(page)

    await page.getByTestId('app-shell-menu-dashboard').click()
    await page.waitForURL('**/#/dashboard')
    await expectMobileSiderCollapsed(page)
  })
})
