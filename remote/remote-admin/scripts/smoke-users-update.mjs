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
const username = `smoke_update_${unique}`;
const password = 'SmokePass123!';
const createdDisplayName = 'Smoke Update User';
const updatedDisplayName = 'Smoke Update User Edited';
const updatedEntitlements = ['dashboard:view', 'publish:run', 'support:read'];
const updatedLicenseExpiry = '2026-12-31T00:00:00Z';
const expectedLicenseExpiryPrefix = updatedLicenseExpiry.replace(/Z$/, '');

if (!artifactDir) {
  throw new Error('Usage: node smoke-users-update.mjs <artifact-dir>');
}

await mkdir(artifactDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1400 } });
const page = await context.newPage();

const result = {
  loginUrl,
  usersUrl,
  username,
  createdUserId: null,
  createPassed: false,
  updateDirectPassed: false,
  updateSensitivePassed: false,
  revokePassed: false,
  restorePassed: false,
  apiVerificationPassed: false,
  screenshots: {
    create: 'create-success.png',
    updateDirect: 'update-direct-success.png',
    updateSensitive: 'update-sensitive-success.png',
    revoke: 'revoke-success.png',
    restoreReloaded: 'restore-reloaded-search.png',
    failure: 'failure-state.png',
  },
  requests: {
    stepUpVerify: [],
    patchUser: [],
    revokeUser: [],
    restoreUser: [],
  },
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
      return;
    }
    if (request.method() === 'POST' && /\/admin\/users\/u_\d+\/revoke$/.test(url.pathname)) {
      result.requests.revokeUser.push({
        path: url.pathname,
        headers: redactHeaders(request.headers()),
      });
      return;
    }
    if (request.method() === 'POST' && /\/admin\/users\/u_\d+\/restore$/.test(url.pathname)) {
      result.requests.restoreUser.push({
        path: url.pathname,
        headers: redactHeaders(request.headers()),
      });
    }
  } catch {
    // Ignore request introspection issues in smoke mode.
  }
});

async function apiJson(path, init = {}) {
  const response = await fetch(`${apiBase}${path}`, init);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status} ${JSON.stringify(payload)}`);
  }
  return payload;
}

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

try {
  await page.goto(loginUrl, { waitUntil: 'networkidle' });
  await page.getByLabel('Username').fill(adminUsername);
  await page.getByLabel('Password').fill(adminPassword);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL(/#\/dashboard$/);

  await page.goto(usersUrl, { waitUntil: 'networkidle' });
  await page.locator('h2.ant-typography').filter({ hasText: 'Users' }).waitFor();

  await page.getByRole('button', { name: 'Create user' }).first().click();
  const createDialog = page.getByRole('dialog', { name: 'Create user' });
  await createDialog.getByLabel('Username').fill(username);
  await createDialog.getByLabel('Initial password').fill(password);
  await createDialog.getByLabel('Display name').fill(createdDisplayName);
  await createDialog.getByLabel('Email').fill(`${username}@example.com`);
  await createDialog.getByLabel('Tenant ID').fill('tenant_smoke_update');
  await createDialog.getByLabel('Entitlements (comma or newline separated)').fill('dashboard:view, publish:run');
  await createDialog.getByRole('button', { name: 'Create user' }).click();

  await page.getByText('Confirm password: Create user').waitFor({ timeout: 20000 });
  await page.getByPlaceholder('Enter your password').fill(adminPassword);
  await page.getByRole('button', { name: 'Confirm and continue' }).click();
  await page.getByText('User created. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText(username).first().waitFor({ timeout: 20000 });
  result.createPassed = true;
  await page.screenshot({ path: join(artifactDir, result.screenshots.create), fullPage: true });

  const displayNameInput = page.getByLabel('Display name').last();
  await displayNameInput.fill(updatedDisplayName);
  await page.getByRole('button', { name: 'Save changes' }).click();
  await page.getByText('User changes saved. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  result.updateDirectPassed = true;
  await page.screenshot({ path: join(artifactDir, result.screenshots.updateDirect), fullPage: true });

  const entitlementsInput = page.getByLabel('Entitlements (comma or newline separated)').last();
  const licenseExpiryInput = page.getByLabel('License expiry (ISO-8601)').last();
  await entitlementsInput.fill(updatedEntitlements.join(', '));
  await licenseExpiryInput.fill(updatedLicenseExpiry);
  await page.getByRole('button', { name: 'Save changes' }).click();
  await page.getByText('Confirm password: Save user changes').waitFor({ timeout: 20000 });
  await page.getByPlaceholder('Enter your password').fill(adminPassword);
  await page.getByRole('button', { name: 'Confirm and continue' }).click();
  await page.getByText('User changes saved. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText('support:read').first().waitFor({ timeout: 20000 });
  result.updateSensitivePassed = true;
  await page.screenshot({ path: join(artifactDir, result.screenshots.updateSensitive), fullPage: true });

  await page.getByRole('button', { name: 'Revoke user' }).click();
  await page.getByText('Confirm password: Revoke user').waitFor({ timeout: 20000 });
  await page.getByPlaceholder('Enter your password').fill(adminPassword);
  await page.getByRole('button', { name: 'Confirm and continue' }).click();
  await page.getByText('User access revoked. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText('Current state: revoked').waitFor({ timeout: 20000 });
  result.revokePassed = true;
  await page.screenshot({ path: join(artifactDir, result.screenshots.revoke), fullPage: true });

  await page.getByRole('button', { name: 'Restore user' }).click();
  await page.getByText('Confirm password: Restore user').waitFor({ timeout: 20000 });
  await page.getByPlaceholder('Enter your password').fill(adminPassword);
  await page.getByRole('button', { name: 'Confirm and continue' }).click();
  await page.getByText('User access restored. The list and detail panel were refreshed from the backend.').waitFor({ timeout: 20000 });
  await page.getByText('Current state: active-or-readable').waitFor({ timeout: 20000 });
  result.restorePassed = true;

  await page.reload({ waitUntil: 'networkidle' });
  await page.locator('h2.ant-typography').filter({ hasText: 'Users' }).waitFor();
  await page.getByPlaceholder('alice / alice@example.com / u_1').fill(username);
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await page.getByText(username).first().waitFor({ timeout: 20000 });
  await page.getByText(updatedDisplayName).first().waitFor({ timeout: 20000 });
  await page.screenshot({ path: join(artifactDir, result.screenshots.restoreReloaded), fullPage: true });

  const loginPayload = await apiJson('/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: adminUsername, password: adminPassword }),
  });
  const adminToken = loginPayload.access_token;
  const listPayload = await apiJson(`/admin/users?q=${encodeURIComponent(username)}`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  if (!Array.isArray(listPayload.items) || listPayload.items.length === 0) {
    throw new Error('API verification could not find the smoke user in /admin/users');
  }
  const createdUser = listPayload.items[0];
  result.createdUserId = createdUser.id;

  const detailPayload = await apiJson(`/admin/users/${createdUser.id}`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });

  const entitlementSet = new Set(detailPayload.entitlements ?? []);
  if (
    detailPayload.username !== username ||
    detailPayload.display_name !== updatedDisplayName ||
    detailPayload.status !== 'active' ||
    detailPayload.license_status !== 'active' ||
    !String(detailPayload.license_expires_at ?? '').startsWith(expectedLicenseExpiryPrefix) ||
    !updatedEntitlements.every((entry) => entitlementSet.has(entry))
  ) {
    throw new Error(`API verification mismatch: ${JSON.stringify(detailPayload)}`);
  }

  result.apiVerificationPassed = true;
  result.apiVerification = {
    listTotal: listPayload.total,
    detail: {
      id: detailPayload.id,
      username: detailPayload.username,
      display_name: detailPayload.display_name,
      status: detailPayload.status,
      license_status: detailPayload.license_status,
      license_expires_at: detailPayload.license_expires_at,
      entitlements: detailPayload.entitlements,
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
    // Ignore failure screenshot errors.
  }
  await writeFile(join(artifactDir, 'result.json'), JSON.stringify(result, null, 2), 'utf8');
  console.error(JSON.stringify(result, null, 2));
  process.exitCode = 1;
} finally {
  await context.close();
  await browser.close();
}
