import { expect, test } from '@playwright/test'

import {
  BASE_URL,
  createCreativeReviewState,
  mockCreativeReviewApis,
} from '../utils/creativeReviewMocks'

test.describe('Creative AIClip workflow', () => {
  test('can submit AIClip output as a new creative version from detail', async ({ page }) => {
    const state = createCreativeReviewState()

    await mockCreativeReviewApis(page, state)

    await page.route('**/api/ai/full-pipeline', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          output_path: 'D:/exports/creative_101_v3.mp4',
        }),
      })
    })

    await page.route('**/api/creative-workflows/101/ai-clip/submit', async (route) => {
      const payload = route.request().postDataJSON() as {
        output_path: string
        source_version_id: number
        title?: string
      }

      const now = '2026-04-17T10:30:00Z'

      state.detail.current_version_id = 203
      state.detail.status = 'WAITING_REVIEW'
      state.detail.updated_at = now
      state.detail.current_version = {
        id: 203,
        version_no: 3,
        title: payload.title ?? 'AIClip 再创作版本',
        parent_version_id: payload.source_version_id,
        package_record_id: 303,
        latest_check: null,
      }
      state.detail.review_summary = {
        current_version_id: undefined,
        current_check: null,
        total_checks: 1,
      }
      state.detail.versions = [
        {
          id: 203,
          creative_item_id: state.detail.id,
          parent_version_id: payload.source_version_id,
          version_no: 3,
          version_type: 'AI_CLIP',
          title: payload.title ?? 'AIClip 再创作版本',
          package_record_id: 303,
          is_current: true,
          latest_check: null,
          created_at: now,
          updated_at: now,
        },
        ...state.detail.versions.map((version) => ({
          ...version,
          is_current: false,
        })),
      ]

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          creative_id: state.detail.id,
          creative_status: state.detail.status,
          source_version_id: payload.source_version_id,
          current_version_id: 203,
          workflow_type: 'ai_clip',
          version: state.detail.versions[0],
          package_record: {
            id: 303,
            creative_version_id: 203,
            package_status: 'READY',
            manifest_json: JSON.stringify({ output_path: payload.output_path }),
            created_at: now,
            updated_at: now,
          },
        }),
      })
    })

    await page.goto(`${BASE_URL}/#/creative/101`)

    await page.getByTestId('creative-open-ai-clip').click()
    await expect(page.getByTestId('creative-ai-clip-drawer')).toBeVisible()

    await page.getByTestId('creative-ai-clip-video-path').fill('D:/videos/source.mp4')
    await page.getByTestId('creative-ai-clip-run-pipeline').click()

    await expect(page.getByTestId('creative-ai-clip-output-path')).toHaveValue('D:/exports/creative_101_v3.mp4')

    await page.getByTestId('creative-ai-clip-submit').click()

    await expect(page.getByTestId('creative-ai-clip-drawer')).toBeHidden()
    await expect(page.getByTestId('creative-version-item-203')).toContainText('V3')
    await expect(page.getByTestId('creative-version-current-203')).toBeVisible()
  })

  test('workbench entry can deep-link directly into the AIClip drawer', async ({ page }) => {
    await mockCreativeReviewApis(page, createCreativeReviewState())

    await page.goto(`${BASE_URL}/#/creative/workbench`)
    await page.getByTestId('creative-workbench-ai-clip-101').click()

    await page.waitForURL('**/#/creative/101?tool=ai-clip')
    await expect(page.getByTestId('creative-ai-clip-drawer')).toBeVisible()
  })

  test('standalone tool route remains available', async ({ page }) => {
    await mockCreativeReviewApis(page, createCreativeReviewState())

    await page.goto(`${BASE_URL}/#/ai-clip`)

    await expect(page.getByTestId('ai-clip-panel')).toBeVisible()
  })
})
