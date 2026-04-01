/**
 * E2E Test Global Setup
 *
 * Prepares the test environment before running tests.
 */

import { chromium, FullConfig } from '@playwright/test'
import fs from 'fs'
import path from 'path'

/**
 * Ensure test data directory exists
 */
function ensureTestDataDir() {
  const testDataDir = path.join(__dirname, '..', 'e2e', 'test-data')
  if (!fs.existsSync(testDataDir)) {
    fs.mkdirSync(testDataDir, { recursive: true })
  }
  return testDataDir
}

/**
 * Create a test account for E2E testing
 * This requires the backend to be running
 */
async function ensureTestAccount() {
  const response = await fetch('http://localhost:8000/api/accounts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      account_id: 'test_account_e2e',
      account_name: 'E2E测试账号',
    }),
  })

  if (response.ok) {
    const data = await response.json()
    console.log('Created test account:', data)
    return data
  }

  // If account already exists, try to get it
  const listResponse = await fetch('http://localhost:8000/api/accounts')
  if (listResponse.ok) {
    const accounts = await listResponse.json()
    const existing = accounts.find(
      (a: { account_id: string }) => a.account_id === 'test_account_e2e'
    )
    if (existing) {
      console.log('Found existing test account:', existing)
      return existing
    }
  }

  console.log('Could not create or find test account')
  return null
}

/**
 * Cleanup function to run before tests
 */
async function globalSetup(config: FullConfig) {
  console.log('Starting E2E test global setup...')

  // Ensure test data directory exists
  const testDataDir = ensureTestDataDir()
  console.log('Test data directory:', testDataDir)

  // Try to create test account (may fail if backend is not ready)
  try {
    await ensureTestAccount()
  } catch (error) {
    console.log('Warning: Could not create test account:', error)
  }

  // Launch browser to apply browser-level permissions/settings
  const browser = await chromium.launch()
  const context = await browser.newContext()
  const page = await context.newPage()

  // Set up browser to handle authentication prompts if needed
  page.on('dialog', async (dialog) => {
    console.log('Browser dialog:', dialog.message())
    await dialog.dismiss()
  })

  await browser.close()

  console.log('E2E test global setup completed')
}

export default globalSetup
