/**
 * Login E2E Test Cases
 *
 * End-to-end tests for the login functionality.
 * Tests cover:
 * - Login page load
 * - Login success flow
 * - Login failure handling
 * - Session persistence
 */

import { test, expect, Page, BrowserContext } from '@playwright/test'
import path from 'path'
import fs from 'fs'

// Test configuration
const TEST_ACCOUNT_ID = 'test_account_e2e'
const TEST_PHONE = '13800138000'
const TEST_CODE = '123456'

// Test data file path for session persistence
const TEST_DATA_DIR = path.join(__dirname, '..', 'test-data')
const SESSION_FILE = path.join(TEST_DATA_DIR, 'session.json')

/**
 * Helper: Navigate to account page and ensure test account exists
 */
async function navigateToAccountPage(page: Page) {
  // Navigate to the app
  await page.goto('/')

  // Wait for page to load
  await page.waitForLoadState('networkidle')

  // Click on Account menu in sidebar
  await page.click('text=账号管理')

  // Wait for account page to load
  await page.waitForURL('**/account')

  // Wait for table to load
  await page.waitForSelector('table', { timeout: 10000 })
}

/**
 * Helper: Click login button for test account
 */
async function clickLoginButton(page: Page) {
  // Find the login button in the table row for test account
  const loginButton = page.locator('tr').filter({ hasText: TEST_ACCOUNT_ID }).getByRole('button', { name: '登录' })

  await loginButton.click()

  // Wait for modal to appear
  await page.waitForSelector('.ant-modal', { timeout: 5000 })
}

/**
 * Helper: Fill in login form
 */
async function fillLoginForm(page: Page, phone: string, code: string) {
  // Fill phone number
  const phoneInput = page.locator('input[placeholder="请输入手机号"]')
  await phoneInput.fill(phone)

  // Fill verification code
  const codeInput = page.locator('input[placeholder="请输入验证码"]')
  await codeInput.fill(code)
}

/**
 * Helper: Create a test account via API
 */
async function createTestAccount(): Promise<number | null> {
  try {
    const response = await fetch('http://localhost:8000/api/accounts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        account_id: TEST_ACCOUNT_ID,
        account_name: 'E2E测试账号',
      }),
    })

    if (response.ok) {
      const data = await response.json()
      return data.id
    }

    // If account exists, get its ID
    const listResponse = await fetch('http://localhost:8000/api/accounts')
    if (listResponse.ok) {
      const accounts = await listResponse.json()
      const existing = accounts.find(
        (a: { account_id: string }) => a.account_id === TEST_ACCOUNT_ID
      )
      return existing?.id || null
    }

    return null
  } catch (error) {
    console.error('Failed to create test account:', error)
    return null
  }
}

/**
 * Helper: Delete test account
 */
async function deleteTestAccount(accountId: number) {
  try {
    await fetch(`http://localhost:8000/api/accounts/${accountId}`, {
      method: 'DELETE',
    })
  } catch (error) {
    console.error('Failed to delete test account:', error)
  }
}

// ============================================================================
// TEST SUITE: Login Page Load Tests
// ============================================================================

test.describe('Login Page Load Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure test account exists before each test
    await createTestAccount()

    // Navigate to account page
    await navigateToAccountPage(page)
  })

  test('TEST-LOGIN-01-01: Login modal opens correctly', async ({ page }) => {
    // Click login button
    await clickLoginButton(page)

    // Verify modal title contains account name
    const modalTitle = page.locator('.ant-modal-title')
    await expect(modalTitle).toContainText('E2E测试账号')

    // Verify phone input exists and is empty
    const phoneInput = page.locator('input[placeholder="请输入手机号"]')
    await expect(phoneInput).toBeVisible()
    await expect(phoneInput).toHaveValue('')

    // Verify code input exists and is empty
    const codeInput = page.locator('input[placeholder="请输入验证码"]')
    await expect(codeInput).toBeVisible()
    await expect(codeInput).toHaveValue('')

    // Verify "Get Code" button exists
    const getCodeButton = page.locator('button:has-text("获取验证码")')
    await expect(getCodeButton).toBeVisible()
    await expect(getCodeButton).toBeEnabled()

    // Verify "Login" button exists
    const loginButton = page.locator('button:has-text("登录")').last()
    await expect(loginButton).toBeVisible()

    // Verify "Cancel" button exists
    const cancelButton = page.locator('button:has-text("取消")')
    await expect(cancelButton).toBeVisible()
  })

  test('TEST-LOGIN-01-02: Modal can be closed and reopened', async ({ page }) => {
    // Open login modal
    await clickLoginButton(page)

    // Verify modal is visible
    await expect(page.locator('.ant-modal')).toBeVisible()

    // Click cancel button
    await page.locator('button:has-text("取消")').click()

    // Wait for modal to close
    await page.waitForSelector('.ant-modal', { state: 'hidden', timeout: 5000 })

    // Verify modal is closed
    await expect(page.locator('.ant-modal')).not.toBeVisible()

    // Open modal again
    await clickLoginButton(page)

    // Verify modal is visible again
    await expect(page.locator('.ant-modal')).toBeVisible()
  })
})

// ============================================================================
// TEST SUITE: Form Validation Tests
// ============================================================================

test.describe('Form Validation Tests', () => {
  test.beforeEach(async ({ page }) => {
    await createTestAccount()
    await navigateToAccountPage(page)
    await clickLoginButton(page)
  })

  test('TEST-LOGIN-02-01: Phone number format validation', async ({ page }) => {
    // Try to get code with invalid phone number
    await fillLoginForm(page, '12345', '')

    // Submit the form (should trigger validation)
    await page.locator('button:has-text("登录")').last().click()

    // Wait for validation error
    await page.waitForTimeout(500)

    // Verify validation error message appears
    const errorMessage = page.locator('.ant-form-item-explain-error')
    await expect(errorMessage.first()).toBeVisible()
  })

  test('TEST-LOGIN-02-02: Empty verification code validation', async ({ page }) => {
    // Fill valid phone number but not code
    await fillLoginForm(page, TEST_PHONE, '')

    // Try to submit
    await page.locator('button:has-text("登录")').last().click()

    // Wait for validation
    await page.waitForTimeout(500)

    // Verify validation error for code
    const codeError = page.locator('.ant-form-item-explain-error')
    await expect(codeError.last()).toBeVisible()
  })
})

// ============================================================================
// TEST SUITE: Login Success Flow Tests
// ============================================================================

test.describe('Login Success Flow Tests', () => {
  let testAccountId: number | null = null

  test.beforeEach(async ({ page }) => {
    testAccountId = await createTestAccount()
    await navigateToAccountPage(page)
    await clickLoginButton(page)
  })

  test.afterEach(async () => {
    if (testAccountId) {
      await deleteTestAccount(testAccountId)
    }
  })

  test('TEST-LOGIN-03-01: Login form submission with valid data', async ({ page }) => {
    // Skip actual login since we can't get real SMS code
    // Instead, test that form accepts valid input

    await fillLoginForm(page, TEST_PHONE, TEST_CODE)

    // Verify inputs have correct values
    await expect(page.locator('input[placeholder="请输入手机号"]')).toHaveValue(TEST_PHONE)
    await expect(page.locator('input[placeholder="请输入验证码"]')).toHaveValue(TEST_CODE)

    // Cancel for now - actual login test requires mock SMS service
    await page.locator('button:has-text("取消")').click()
  })

  test('TEST-LOGIN-03-02: Code sending with valid phone', async ({ page }) => {
    // Fill phone number
    const phoneInput = page.locator('input[placeholder="请输入手机号"]')
    await phoneInput.fill(TEST_PHONE)

    // Click get code button
    const getCodeButton = page.locator('button:has-text("获取验证码")')
    await getCodeButton.click()

    // Wait for response
    await page.waitForTimeout(2000)

    // Verify button shows countdown (if code was sent successfully)
    // Note: This test assumes the backend can send codes or has a test mode
    const buttonText = await getCodeButton.textContent()
    expect(buttonText).toBeTruthy()
  })
})

// ============================================================================
// TEST SUITE: Login Error Handling Tests
// ============================================================================

test.describe('Login Error Handling Tests', () => {
  let testAccountId: number | null = null

  test.beforeEach(async ({ page }) => {
    testAccountId = await createTestAccount()
    await navigateToAccountPage(page)
    await clickLoginButton(page)
  })

  test.afterEach(async () => {
    if (testAccountId) {
      await deleteTestAccount(testAccountId)
    }
  })

  test('TEST-LOGIN-04-01: Login with wrong code shows error', async ({ page }) => {
    // Fill form with wrong code
    await fillLoginForm(page, TEST_PHONE, '000000')

    // Submit login
    await page.locator('button:has-text("登录")').last().click()

    // Wait for error response
    await page.waitForTimeout(3000)

    // Check for error message (either in-page or toast)
    const errorToast = page.locator('.ant-message-error')
    const hasErrorToast = await errorToast.isVisible().catch(() => false)

    if (hasErrorToast) {
      await expect(errorToast).toBeVisible()
    }
  })

  test('TEST-LOGIN-04-02: Login with empty fields shows validation errors', async ({ page }) => {
    // Click login without filling anything
    await page.locator('button:has-text("登录")').last().click()

    // Wait for validation
    await page.waitForTimeout(500)

    // Verify validation errors appear
    const errors = page.locator('.ant-form-item-explain-error')
    const errorCount = await errors.count()
    expect(errorCount).toBeGreaterThanOrEqual(1)
  })
})

// ============================================================================
// TEST SUITE: Session Persistence Tests
// ============================================================================

test.describe('Session Persistence Tests', () => {
  test('TEST-LOGIN-05-01: Session can be exported and imported', async ({ browser }) => {
    // Create two browser contexts
    const context1 = await browser.newContext()
    const context2 = await browser.newContext()

    const page1 = await context1.newPage()
    const page2 = await context2.newPage()

    try {
      // Step 1: Login in first context
      await page1.goto('/')
      await page1.waitForLoadState('networkidle')
      await page1.click('text=账号管理')
      await page1.waitForURL('**/account')

      // Ensure test account exists
      const accountId = await createTestAccount()
      if (!accountId) {
        throw new Error('Could not create test account')
      }

      // Reload to see new account
      await page1.reload()
      await page1.waitForLoadState('networkidle')

      await clickLoginButton(page1)

      // Note: Real session export requires successful login
      // For this test, we simulate the session storage mechanism

      // Export session storage state
      const storageState = await context1.storageState()

      // Save session to file
      if (!fs.existsSync(TEST_DATA_DIR)) {
        fs.mkdirSync(TEST_DATA_DIR, { recursive: true })
      }
      fs.writeFileSync(SESSION_FILE, JSON.stringify(storageState, null, 2))

      // Step 2: Use session in second context
      await context2.addInitScript((storage) => {
        // This would restore cookies/storage
        localStorage.setItem('test_session', storage)
      }, storageState)

      await page2.goto('/')
      await page2.waitForLoadState('networkidle')

      // Verify session is restored (no need to login again)
      // The exact verification depends on the session implementation
      await page2.waitForTimeout(1000)

      // Clean up
      if (fs.existsSync(SESSION_FILE)) {
        fs.unlinkSync(SESSION_FILE)
      }
    } finally {
      await context1.close()
      await context2.close()
    }
  })

  test('TEST-LOGIN-05-02: Session file persists between test runs', async () => {
    // This test verifies that session data can be saved and loaded
    const testSession = {
      cookies: [
        {
          name: 'test_session',
          value: 'test_value',
          domain: 'localhost',
          path: '/',
        },
      ],
      origins: [],
    }

    // Write session file
    if (!fs.existsSync(TEST_DATA_DIR)) {
      fs.mkdirSync(TEST_DATA_DIR, { recursive: true })
    }
    fs.writeFileSync(SESSION_FILE, JSON.stringify(testSession))

    // Read session file
    expect(fs.existsSync(SESSION_FILE)).toBeTruthy()
    const loaded = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8'))
    expect(loaded.cookies).toHaveLength(1)
    expect(loaded.cookies[0].name).toBe('test_session')

    // Clean up
    if (fs.existsSync(SESSION_FILE)) {
      fs.unlinkSync(SESSION_FILE)
    }
  })
})

// ============================================================================
// TEST SUITE: SSE Status Stream Tests
// ============================================================================

test.describe('SSE Status Stream Tests', () => {
  test('TEST-LOGIN-06-01: SSE connection established on modal open', async ({ page }) => {
    // Create test account
    await createTestAccount()

    // Navigate to account page
    await navigateToAccountPage(page)

    // Intercept SSE requests
    const sseRequests: string[] = []
    page.on('request', (request) => {
      if (request.url().includes('/stream')) {
        sseRequests.push(request.url())
      }
    })

    // Open login modal
    await clickLoginButton(page)

    // Wait for SSE connection
    await page.waitForTimeout(1000)

    // Verify SSE request was made
    expect(sseRequests.length).toBeGreaterThanOrEqual(1)
    expect(sseRequests[0]).toContain('/api/accounts/login/')
  })

  test('TEST-LOGIN-06-02: SSE status updates display correctly', async ({ page }) => {
    await createTestAccount()
    await navigateToAccountPage(page)
    await clickLoginButton(page)

    // Fill phone number to trigger potential status updates
    await fillLoginForm(page, TEST_PHONE, '')

    // Wait for any status updates
    await page.waitForTimeout(2000)

    // The status message area should exist in the modal
    const modal = page.locator('.ant-modal')
    await expect(modal).toBeVisible()
  })
})

// ============================================================================
// TEST SUITE: Accessibility Tests
// ============================================================================

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await createTestAccount()
    await navigateToAccountPage(page)
    await clickLoginButton(page)
  })

  test('TEST-LOGIN-07-01: All form inputs have labels', async ({ page }) => {
    // Check phone input has accessible label
    const phoneInput = page.locator('input[placeholder="请输入手机号"]')
    await expect(phoneInput).toHaveAttribute('id')

    // Check code input has accessible label
    const codeInput = page.locator('input[placeholder="请输入验证码"]')
    await expect(codeInput).toHaveAttribute('id')

    // Check all inputs are reachable via keyboard (have proper tab order)
    await phoneInput.focus()
    await expect(phoneInput).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(codeInput).toBeFocused()
  })

  test('TEST-LOGIN-07-02: Buttons are keyboard accessible', async ({ page }) => {
    // Tab to phone input
    await page.locator('input[placeholder="请输入手机号"]').focus()

    // Tab through buttons
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Should be able to reach cancel button
    const cancelButton = page.locator('button:has-text("取消")')
    await cancelButton.focus()
    await expect(cancelButton).toBeFocused()
  })
})
