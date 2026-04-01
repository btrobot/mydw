/**
 * E2E Test Global Teardown
 *
 * Cleans up after all tests have completed.
 */

import { chromium, FullConfig } from '@playwright/test'
import fs from 'fs'
import path from 'path'

/**
 * Clean up test artifacts
 */
async function cleanupTestArtifacts() {
  const testDataDir = path.join(__dirname, '..', 'e2e', 'test-data')

  // Clean up old test data (keep recent ones for debugging)
  if (fs.existsSync(testDataDir)) {
    try {
      const files = fs.readdirSync(testDataDir)
      const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000

      for (const file of files) {
        const filePath = path.join(testDataDir, file)
        const stats = fs.statSync(filePath)
        if (stats.mtimeMs < oneWeekAgo) {
          fs.unlinkSync(filePath)
          console.log('Removed old test artifact:', file)
        }
      }
    } catch (error) {
      console.log('Warning: Could not clean up test artifacts:', error)
    }
  }
}

/**
 * Close any remaining browser contexts
 */
async function closeBrowser() {
  try {
    const browser = await chromium.launch()
    await browser.close()
  } catch {
    // Browser may already be closed
  }
}

/**
 * Main teardown function
 */
async function globalTeardown(config: FullConfig) {
  console.log('Starting E2E test global teardown...')

  // Clean up test artifacts
  await cleanupTestArtifacts()

  // Close browser if still open
  await closeBrowser()

  console.log('E2E test global teardown completed')
}

export default globalTeardown
