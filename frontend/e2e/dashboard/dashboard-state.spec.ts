import { expect, test, type Page } from '@playwright/test'

import { createAuthSession } from '../utils/workbenchEntryMocks'

const BASE_URL = process.env.E2E_BASE_URL || ''

interface DashboardMockOptions {
  publishStatusCode?: number
  taskStatsStatusCode?: number
  systemStatsStatusCode?: number
  logsStatusCode?: number
}

async function mockDashboardShell(page: Page, options: DashboardMockOptions = {}) {
  const {
    publishStatusCode = 200,
    taskStatsStatusCode = 200,
    systemStatsStatusCode = 200,
    logsStatusCode = 200,
  } = options

  await page.route('**/api/auth/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(createAuthSession('authenticated_active')),
    })
  })

  await page.route('**/api/publish/status', async (route) => {
    await route.fulfill({
      status: publishStatusCode,
      contentType: 'application/json',
      body: JSON.stringify(
        publishStatusCode >= 400
          ? { detail: 'publish status failed' }
          : {
              status: 'idle',
              current_task_id: null,
              total_pending: 0,
              total_success: 0,
              total_failed: 0,
              scheduler_mode: 'task',
              effective_scheduler_mode: 'task',
              publish_pool_kill_switch: false,
              publish_pool_shadow_read: false,
              scheduler_shadow_diff: null,
            },
      ),
    })
  })

  await page.route('**/api/tasks/stats**', async (route) => {
    await route.fulfill({
      status: taskStatsStatusCode,
      contentType: 'application/json',
      body: JSON.stringify(
        taskStatsStatusCode >= 400
          ? { detail: 'task stats failed' }
          : {
              total: 0,
              draft: 0,
              composing: 0,
              ready: 0,
              uploading: 0,
              uploaded: 0,
              failed: 0,
              cancelled: 0,
              today_uploaded: 0,
            },
      ),
    })
  })

  await page.route('**/api/system/stats**', async (route) => {
    await route.fulfill({
      status: systemStatsStatusCode,
      contentType: 'application/json',
      body: JSON.stringify(
        systemStatsStatusCode >= 400
          ? { detail: 'system stats failed' }
          : {
              total_accounts: 1,
              active_accounts: 1,
              total_products: 0,
            },
      ),
    })
  })

  await page.route('**/api/system/logs**', async (route) => {
    await route.fulfill({
      status: logsStatusCode,
      contentType: 'application/json',
      body: JSON.stringify(
        logsStatusCode >= 400
          ? { detail: 'system logs failed' }
          : { items: [] },
      ),
    })
  })
}

test.describe('Dashboard state contract', () => {
  test('keeps dashboard as diagnostics surface while showing explicit success and empty states', async ({ page }) => {
    await mockDashboardShell(page)
    await page.goto(`${BASE_URL}/#/dashboard`)

    await expect(page.getByTestId('dashboard-primary-cta')).toBeVisible()
    await expect(page.getByText('运行与发布总览')).toBeVisible()
    await expect(page.getByText('日常作品处理请进入工作台')).toBeVisible()

    await expect(page.getByTestId('dashboard-task-stats-empty')).toBeVisible()
    await expect(page.getByTestId('dashboard-publish-status-success')).toBeVisible()
    await expect(page.getByTestId('dashboard-system-stats-success')).toBeVisible()
    await expect(page.getByTestId('dashboard-logs-empty')).toBeVisible()
    await expect(page.getByTestId('dashboard-publish-status-success')).toContainText('空闲')
    await expect(page.getByTestId('dashboard-system-stats-success')).toContainText('账号')
  })

  test('shows runtime request failures as explicit errors instead of fallback defaults', async ({ page }) => {
    await mockDashboardShell(page, {
      publishStatusCode: 500,
      taskStatsStatusCode: 500,
      systemStatsStatusCode: 500,
      logsStatusCode: 500,
    })
    await page.goto(`${BASE_URL}/#/dashboard`)

    await expect(page.getByTestId('dashboard-task-stats-error')).toBeVisible()
    await expect(page.getByTestId('dashboard-publish-status-error')).toBeVisible()
    await expect(page.getByTestId('dashboard-system-stats-error')).toBeVisible()
    await expect(page.getByTestId('dashboard-logs-error')).toBeVisible()

    await expect(page.getByTestId('dashboard-task-stats-empty')).toHaveCount(0)
    await expect(page.getByTestId('dashboard-publish-status-success')).toHaveCount(0)
    await expect(page.getByTestId('dashboard-system-stats-success')).toHaveCount(0)
    await expect(page.getByTestId('dashboard-logs-empty')).toHaveCount(0)
  })
})
