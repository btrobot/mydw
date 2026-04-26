import { chromium } from '../../../frontend/node_modules/playwright/index.mjs';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const artifactDir = process.argv[2];
const apiBase = 'http://127.0.0.1:8100';
const appBase = 'http://127.0.0.1:4173/dist-react/index.html?apiBase=http://127.0.0.1:8100';
const loginUrl = `${appBase}#/login`;
const usersUrl = `${appBase}#/users`;
const adminUsername = 'admin';
const adminPassword = 'admin-secret';
const unique = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
const usernamePrefix = `smoke_multi_update_${unique}`;
const userA = {
  username: `${usernamePrefix}_a`,
  password: 'SmokePass123!',
  displayName: 'Smoke Multi User A',
  email: `${usernamePrefix}_a@example.com`,
  tenantId: 'tenant_smoke_multi',
  entitlements: ['dashboard:view'],
};
const userB = {
  username: `${usernamePrefix}_b`,
  password: 'SmokePass123!',
  displayName: 'Smoke Multi User B',
  email: `${usernamePrefix}_b@example.com`,
  tenantId: 'tenant_smoke_multi',
  entitlements: ['users:read'],
};
const userBUpdatedDisplayName = 'Smoke Multi User B Edited';
const userBUpdatedEntitlements = ['dashboard:view', 'publish:run', 'support:read'];
const userBUpdatedLicenseExpiry = '2026-12-31T00:00:00Z';
const expectedLicenseExpiryPrefix = userBUpdatedLicenseExpiry.replace(/Z$/, '');

if (!artifactDir) {
  throw new Error('Usage: node smoke-users-update-multi.mjs <artifact-dir>');
}

await mkdir(artifactDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1600 } });
const page = await context.newPage();

const result = {
  loginUrl,
  usersUrl,
  usernamePrefix,
  createdUsers: [],
  loginPassed: false,
  createUsersPassed: false,
  switchDraftIsolationPassed: false,
  resetPassed: false,
  updateDirectPassed: false,
  updateSensitivePassed: false,
  apiVerificationPassed: false,
  screenshots: {
    filteredList: 'filtered-two-users.png',
    switchIsolation: 'switch-isolation-clean-b.png',
    resetRestored: 'reset-restored-a.png',
    updateDirect: 'update-direct-b.png',
    updateSensitive: 'update-sensitive-b.png',
    failure: 'failure-state.png',
  },
  requests: {
    stepUpVerify: [],
    patchUser: [],
  },
  checkpoints: {},
  timestamps: {
    startedAt: new Date().toISOString(),
  },
};

page.on('request', (request) => {
  try {
    const url = new URL(request.url());
    if (url.origin !== apiBase) {
      return;
    }
    if (request.method() === 'POST' && url.pathname === '/admin/step-up/password/verify') {
      result.requests.stepUpVerify.push({
        path: url.pathname,
        headers: redactHeaders(request.headers()),
        body: request.postDataJSON(),
      });
      return;
    }
    if (request.method() === 'PATCH' && /\/admin\/users\/u_\d+$/.test(url.pathname)) {
      result.requests.patchUser.push({
        path: url.pathname,
        headers: redactHeaders(request.headers()),
        body: request.postDataJSON(),
      });
    }
  } catch {
    // Ignore smoke capture issues.
  }
});

function redactHeaders(headers) {
  if (!headers || typeof headers !== 'object') {
    return headers;
  }
  const redacted = { ...headers };
  if (typeof redacted.authorization === 'string') {
    redacted.authorization = 'Bearer <redacted>';
  }
  if (typeof redacted['x-step-up-token'] === 'string') {
    redacted['x-step-up-token'] = '<redacted>';
  }
  return redacted;
}

async function apiJson(path, init = {}) {
  const response = await fetch(`${apiBase}${path}`, init);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status} ${JSON.stringify(payload)}`);
  }
  return payload;
}

function usersListCard() {
  return page.locator('.ant-card').filter({ hasText: /^Users \(\d+\)/ }).first();
}

function selectedUserCard() {
  return page.locator('.ant-card').filter({ hasText: 'Selected user' }).first();
}

function displayNameInput() {
  return page.getByLabel('Display name').last();
}

function entitlementsInput() {
  return page.getByLabel('Entitlements (comma or newline separated)').last();
}

function licenseExpiryInput() {
  return page.getByLabel('License expiry (ISO-8601)').last();
}

async function loginAsAdmin() {
  await page.goto(loginUrl, { waitUntil: 'networkidle' });
  await page.getByLabel('Username').fill(adminUsername);
  await page.getByLabel('Password').fill(adminPassword);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL(/#\/dashboard$/);
  result.loginPassed = true;
}

async function openUsersPage() {
  await page.goto(usersUrl, { waitUntil: 'networkidle' });
  await page.locator('h2.ant-typography').filter({ hasText: 'Users' }).waitFor();
}

async function createUserViaUi(user) {
  await page.getByRole('button', { name: 'Create user' }).first().click();
  const createDialog = page.getByRole('dialog', { name: 'Create user' });
  await createDialog.getByLabel('Username').fill(user.username);
  await createDialog.getByLabel('Initial password').fill(user.password);
  await createDialog.getByLabel('Display name').fill(user.displayName);
  await createDialog.getByLabel('Email').fill(user.email);
  await createDialog.getByLabel('Tenant ID').fill(user.tenantId);
  await createDialog.getByLabel('Entitlements (comma or newline separated)').fill(user.entitlements.join(', '));
  await createDialog.getByRole('button', { name: 'Create user' }).click();
  await page.getByText('Confirm password: Create user').waitFor({ timeout: 20000 });
  await page.getByPlaceholder('Enter your password').fill(adminPassword);
  await page.getByRole('button', { name: 'Confirm and continue' }).click();
  await page.getByText('User created. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText(user.username).first().waitFor({ timeout: 20000 });
}

async function applySearch(query) {
  const input = page.getByPlaceholder('alice / alice@example.com / u_1');
  await input.fill(query);
  await page.getByRole('button', { name: 'Apply filters' }).click();
}

async function selectUserFromList(user) {
  const listCard = usersListCard();
  await listCard.getByText(user.displayName, { exact: true }).first().click();
  await selectedUserCard().getByText(user.username, { exact: true }).waitFor({ timeout: 20000 });
}

async function assertSelectedUserState(user) {
  await selectedUserCard().getByText(user.username, { exact: true }).waitFor({ timeout: 20000 });
  const currentDisplayName = await displayNameInput().inputValue();
  const currentEntitlements = await entitlementsInput().inputValue();
  if (currentDisplayName !== user.displayName) {
    throw new Error(`Expected selected display name ${user.displayName}, got ${currentDisplayName}`);
  }
  if (currentEntitlements !== user.entitlements.join(', ')) {
    throw new Error(`Expected selected entitlements ${user.entitlements.join(', ')}, got ${currentEntitlements}`);
  }
}

try {
  await loginAsAdmin();
  await openUsersPage();

  await createUserViaUi(userA);
  await createUserViaUi(userB);
  result.createUsersPassed = true;

  await applySearch(usernamePrefix);
  await page.getByText(userA.username).first().waitFor({ timeout: 20000 });
  await page.getByText(userB.username).first().waitFor({ timeout: 20000 });
  await page.screenshot({ path: join(artifactDir, result.screenshots.filteredList), fullPage: true });

  result.checkpoints.patchCountBeforeSwitch = result.requests.patchUser.length;
  await selectUserFromList(userA);
  await displayNameInput().fill('Smoke Draft A');
  await entitlementsInput().fill('dashboard:view, dirty:a');

  await selectUserFromList(userB);
  await assertSelectedUserState(userB);
  result.checkpoints.patchCountAfterSwitchToB = result.requests.patchUser.length;
  if (result.checkpoints.patchCountAfterSwitchToB !== result.checkpoints.patchCountBeforeSwitch) {
    throw new Error('Switching from user A to user B emitted an unexpected PATCH request');
  }
  await page.screenshot({ path: join(artifactDir, result.screenshots.switchIsolation), fullPage: true });

  await selectUserFromList(userA);
  await assertSelectedUserState(userA);
  result.switchDraftIsolationPassed = true;

  await displayNameInput().fill('Smoke Reset A');
  await entitlementsInput().fill('dashboard:view, dirty:reset');
  await page.getByRole('button', { name: 'Reset' }).click();
  await assertSelectedUserState(userA);
  result.checkpoints.patchCountAfterReset = result.requests.patchUser.length;
  if (result.checkpoints.patchCountAfterReset !== result.checkpoints.patchCountBeforeSwitch) {
    throw new Error('Reset emitted an unexpected PATCH request');
  }
  result.resetPassed = true;
  await page.screenshot({ path: join(artifactDir, result.screenshots.resetRestored), fullPage: true });

  await selectUserFromList(userB);
  await displayNameInput().fill(userBUpdatedDisplayName);
  await page.getByRole('button', { name: 'Save changes' }).click();
  await page.getByText('User changes saved. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText(userBUpdatedDisplayName).first().waitFor({ timeout: 20000 });
  result.updateDirectPassed = true;
  await page.screenshot({ path: join(artifactDir, result.screenshots.updateDirect), fullPage: true });

  await entitlementsInput().fill(userBUpdatedEntitlements.join(', '));
  await licenseExpiryInput().fill(userBUpdatedLicenseExpiry);
  await page.getByRole('button', { name: 'Save changes' }).click();
  await page.getByText('Confirm password: Save user changes').waitFor({ timeout: 20000 });
  await page.getByPlaceholder('Enter your password').fill(adminPassword);
  await page.getByRole('button', { name: 'Confirm and continue' }).click();
  await page.getByText('User changes saved. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText('support:read').first().waitFor({ timeout: 20000 });
  result.updateSensitivePassed = true;
  await page.screenshot({ path: join(artifactDir, result.screenshots.updateSensitive), fullPage: true });

  const loginPayload = await apiJson('/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: adminUsername, password: adminPassword }),
  });
  const adminToken = loginPayload.access_token;
  const listPayload = await apiJson(`/admin/users?q=${encodeURIComponent(usernamePrefix)}`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  const items = Array.isArray(listPayload.items) ? listPayload.items : [];
  if (items.length < 2) {
    throw new Error(`API verification expected 2 smoke users, got ${items.length}`);
  }

  const apiUserA = items.find((item) => item.username === userA.username);
  const apiUserB = items.find((item) => item.username === userB.username);
  if (!apiUserA || !apiUserB) {
    throw new Error(`API verification could not find both smoke users: ${JSON.stringify(items)}`);
  }

  const detailA = await apiJson(`/admin/users/${apiUserA.id}`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  const detailB = await apiJson(`/admin/users/${apiUserB.id}`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });

  const entitlementSetB = new Set(detailB.entitlements ?? []);
  if (
    detailA.display_name !== userA.displayName ||
    JSON.stringify(detailA.entitlements ?? []) !== JSON.stringify(userA.entitlements) ||
    detailB.display_name !== userBUpdatedDisplayName ||
    detailB.status !== 'active' ||
    detailB.license_status !== 'active' ||
    !String(detailB.license_expires_at ?? '').startsWith(expectedLicenseExpiryPrefix) ||
    !userBUpdatedEntitlements.every((entry) => entitlementSetB.has(entry))
  ) {
    throw new Error(`API verification mismatch: ${JSON.stringify({ detailA, detailB })}`);
  }

  result.createdUsers = [
    { id: detailA.id, username: detailA.username, display_name: detailA.display_name },
    { id: detailB.id, username: detailB.username, display_name: detailB.display_name },
  ];
  result.apiVerificationPassed = true;
  result.apiVerification = {
    listTotal: listPayload.total,
    detailA: {
      id: detailA.id,
      username: detailA.username,
      display_name: detailA.display_name,
      entitlements: detailA.entitlements,
    },
    detailB: {
      id: detailB.id,
      username: detailB.username,
      display_name: detailB.display_name,
      status: detailB.status,
      license_status: detailB.license_status,
      license_expires_at: detailB.license_expires_at,
      entitlements: detailB.entitlements,
    },
  };

  result.timestamps.finishedAt = new Date().toISOString();
  await writeFile(join(artifactDir, 'result.json'), JSON.stringify(result, null, 2), 'utf8');
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  result.timestamps.failedAt = new Date().toISOString();
  result.error = {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : null,
  };
  try {
    await page.screenshot({ path: join(artifactDir, result.screenshots.failure), fullPage: true });
  } catch {
    // Ignore screenshot failures in smoke mode.
  }
  await writeFile(join(artifactDir, 'result.json'), JSON.stringify(result, null, 2), 'utf8');
  console.error(JSON.stringify(result, null, 2));
  process.exitCode = 1;
} finally {
  await context.close();
  await browser.close();
}
