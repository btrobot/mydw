import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

import { chromium } from '../../../frontend/node_modules/playwright/index.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REMOTE_ADMIN_DIR = join(__dirname, '..');
const DIST_REACT_DIR = join(REMOTE_ADMIN_DIR, 'dist-react');
const ACCESS_TOKEN_KEY = 'remote_admin_access_token';
const API_BASE = 'http://127.0.0.1:8100';

const ADMIN_SESSION = {
  session_id: 'admin_sess_1',
  expires_at: '2026-05-01T00:00:00Z',
  user: {
    id: 'admin_1',
    username: 'admin',
    display_name: 'Remote Admin',
    role: 'super_admin',
  },
};

const ACTIVE_USER = {
  id: 'u_1',
  username: 'alice',
  display_name: 'Alice',
  email: 'alice@example.com',
  tenant_id: 'tenant_1',
  status: 'active',
  license_status: 'active',
  license_expires_at: '2026-07-01T00:00:00Z',
  entitlements: ['dashboard:view'],
  device_count: 1,
  last_seen_at: '2026-04-30T00:00:00Z',
};

const REVOKED_USER = {
  ...ACTIVE_USER,
  status: 'revoked',
  license_status: 'revoked',
};

const SECOND_USER = {
  id: 'u_2',
  username: 'bob',
  display_name: 'Bob',
  email: 'bob@example.com',
  tenant_id: 'tenant_2',
  status: 'active',
  license_status: 'disabled',
  license_expires_at: null,
  entitlements: ['users:read'],
  device_count: 2,
  last_seen_at: '2026-04-29T00:00:00Z',
};

const ACTIVE_DEVICE = {
  device_id: 'device_1',
  user_id: 'u_1',
  device_status: 'bound',
  first_bound_at: '2026-04-01T00:00:00Z',
  last_seen_at: '2026-04-30T00:00:00Z',
  client_version: '0.2.0',
};

const UNBOUND_DEVICE = {
  ...ACTIVE_DEVICE,
  user_id: null,
  device_status: 'unbound',
};

const ACTIVE_SESSION = {
  session_id: 'sess_1',
  user_id: 'u_1',
  device_id: 'device_1',
  auth_state: 'authenticated_active',
  issued_at: '2026-04-01T00:00:00Z',
  expires_at: '2026-05-01T00:00:00Z',
  last_seen_at: '2026-04-30T00:00:00Z',
};

const CONTENT_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
};

let staticServer;
let appBaseUrl;

test.before(async () => {
  const started = await startStaticServer(DIST_REACT_DIR);
  staticServer = started.server;
  appBaseUrl = started.baseUrl;
});

test.after(async () => {
  if (staticServer) {
    await new Promise((resolve, reject) => {
      staticServer.close((error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      });
    });
  }
});

test('users page opens a password-confirmation modal before revoke', async () => {
  const harness = await openUsersStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Revoke user' }).click();
    await harness.page.getByText('Confirm password: Revoke user').waitFor();
    await harness.page.getByText(
      'Confirm your password before revoking this user. The admin API will issue a short-lived step-up token for the destructive request.'
    ).waitFor();
  } finally {
    await harness.close();
  }
});

test('users step-up success submits verify request and forwards step-up token header', async () => {
  const harness = await openUsersStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Revoke user' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'User access revoked. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.verifyBodies.length, 1);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'users.write',
    });
    assert.equal(harness.calls.verifyHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.verifyHeaders[0]['content-type'], 'application/json');
    assert.equal(harness.calls.revokeHeaders.length, 1);
    assert.equal(harness.calls.revokeHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.revokeHeaders[0]['x-step-up-token'], 'admin_step_up_1');
    await harness.page.getByText('Current state: revoked').waitFor();
  } finally {
    await harness.close();
  }
});

test('users step-up verification failure keeps modal open and blocks revoke', async () => {
  const harness = await openUsersStepUpHarness({
    verifyResponses: [
      {
        status: 401,
        body: {
          error_code: 'invalid_credentials',
          message: 'Invalid password',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Revoke user' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('wrong-password');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText('Incorrect password. Please retry.').waitFor();
    await harness.page.getByText('Confirm password: Revoke user').waitFor();
    assert.equal(harness.calls.revokeHeaders.length, 0);
  } finally {
    await harness.close();
  }
});

test('users step-up token expiry redirects back to login with auth notice', async () => {
  const harness = await openUsersStepUpHarness({
    verifyResponses: [
      {
        status: 401,
        body: {
          error_code: 'token_expired',
          message: 'Session expired',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Revoke user' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.waitForURL(/#\/login$/);
    await harness.page.getByText('Your admin session expired. Please sign in again.').waitFor();
    assert.equal(harness.calls.revokeHeaders.length, 0);
  } finally {
    await harness.close();
  }
});

test('users restore step-up reactivates a revoked user with the same token flow', async () => {
  const harness = await openUsersStepUpHarness({
    initialUser: REVOKED_USER,
  });

  try {
    await harness.page.getByRole('button', { name: 'Restore user' }).click();
    await harness.page.getByText('Confirm password: Restore user').waitFor();
    await harness.page.getByText(
      'Confirm your password before restoring this user. The admin API will issue a short-lived step-up token for the destructive request.'
    ).waitFor();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'User access restored. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.verifyBodies.length, 1);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'users.write',
    });
    assert.equal(harness.calls.restoreHeaders.length, 1);
    assert.equal(harness.calls.restoreHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.restoreHeaders[0]['x-step-up-token'], 'admin_step_up_1');
    await harness.page.getByText('Current state: active-or-readable').waitFor();
  } finally {
    await harness.close();
  }
});

test('users revoke removes the selected row from an active-only filter without leaving stale detail', async () => {
  const harness = await openUsersStepUpHarness();

  try {
    await applyUsersStatusFilter(harness.page, 'active');
    await harness.page.getByText('Alice').first().waitFor();

    await harness.page.getByRole('button', { name: 'Revoke user' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText('Users (0)').waitFor();
    await harness.page.getByText('No users matched the current filters.').waitFor();
    await harness.page.getByText('Select a user from the list to review authorization detail.').waitFor();
    assert.equal(harness.calls.revokeHeaders.length, 1);
  } finally {
    await harness.close();
  }
});

test('users display-name update saves without step-up and refreshes list/detail state', async () => {
  const harness = await openUsersStepUpHarness();

  try {
    const displayNameInput = harness.page.getByLabel('Display name');
    await displayNameInput.fill('Alice Updated');
    await harness.page.getByRole('button', { name: 'Save changes' }).click();

    await harness.page.getByText(
      'User changes saved. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.verifyBodies.length, 0);
    assert.equal(harness.calls.updateRequests.length, 1);
    assert.equal(harness.calls.updateRequests[0].headers.authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.updateRequests[0].headers['x-step-up-token'], undefined);
    assert.deepEqual(harness.calls.updateRequests[0].body, {
      display_name: 'Alice Updated',
    });
    await harness.page.getByText('Alice Updated').first().waitFor();
  } finally {
    await harness.close();
  }
});

test('users reset restores the selected detail draft without issuing an update request', async () => {
  const harness = await openUsersStepUpHarness();

  try {
    const displayNameInput = harness.page.getByLabel('Display name');
    const entitlementsInput = harness.page.getByLabel('Entitlements (comma or newline separated)');

    await displayNameInput.fill('Alice Draft');
    await entitlementsInput.fill('dashboard:view, publish:run');
    await harness.page.getByRole('button', { name: 'Reset' }).click();

    assert.equal(await displayNameInput.inputValue(), 'Alice');
    assert.equal(await entitlementsInput.inputValue(), 'dashboard:view');
    assert.equal(harness.calls.updateRequests.length, 0);
  } finally {
    await harness.close();
  }
});

test('users update can clear license expiry after backend step-up confirmation', async () => {
  const harness = await openUsersStepUpHarness({
    updateResponses: [
      {
        status: 403,
        body: {
          error_code: 'step_up_required',
          message: 'Step-up verification required',
        },
      },
    ],
  });

  try {
    await harness.page.getByLabel('License expiry (ISO-8601)').fill('');
    await harness.page.getByRole('button', { name: 'Save changes' }).click();

    await harness.page.getByText('Confirm password: Save user changes').waitFor();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'User changes saved. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.updateRequests.length, 2);
    assert.deepEqual(harness.calls.updateRequests[0].body, {
      license_expires_at: null,
    });
    assert.equal(harness.calls.updateRequests[1].headers['x-step-up-token'], 'admin_step_up_1');
    assert.deepEqual(harness.calls.updateRequests[1].body, {
      license_expires_at: null,
    });
  } finally {
    await harness.close();
  }
});

test('users restore removes the selected row from a revoked-only filter and reappears after clearing filters', async () => {
  const harness = await openUsersStepUpHarness({
    initialUser: REVOKED_USER,
  });

  try {
    await applyUsersStatusFilter(harness.page, 'revoked');
    await harness.page.getByText('Alice').first().waitFor();
    await harness.page.getByText('Current state: revoked').waitFor();

    await harness.page.getByRole('button', { name: 'Restore user' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText('Users (0)').waitFor();
    await harness.page.getByText('No users matched the current filters.').waitFor();
    await harness.page.getByText('Select a user from the list to review authorization detail.').waitFor();

    await harness.page.getByRole('button', { name: 'Clear' }).click();
    await harness.page.getByText('Alice').first().waitFor();
    await harness.page.getByText('Current state: active-or-readable').waitFor();
    assert.equal(harness.calls.restoreHeaders.length, 1);
  } finally {
    await harness.close();
  }
});

test('users switching selection replaces unsaved edits with the newly selected detail state', async () => {
  const harness = await openUsersStepUpHarness({
    initialUsers: [ACTIVE_USER, SECOND_USER],
  });

  try {
    const displayNameInput = harness.page.getByLabel('Display name');
    const entitlementsInput = harness.page.getByLabel('Entitlements (comma or newline separated)');

    await displayNameInput.fill('Alice Draft');
    await entitlementsInput.fill('dashboard:view, publish:run');

    await harness.page.getByText('Bob').first().click();
    await harness.page.getByText('bob@example.com').first().waitFor();

    assert.equal(await displayNameInput.inputValue(), 'Bob');
    assert.equal(await entitlementsInput.inputValue(), 'users:read');
    assert.equal(harness.calls.updateRequests.length, 0);

    await harness.page.getByText('Alice').first().click();
    await harness.page.getByText('alice@example.com').first().waitFor();

    assert.equal(await displayNameInput.inputValue(), 'Alice');
    assert.equal(await entitlementsInput.inputValue(), 'dashboard:view');
  } finally {
    await harness.close();
  }
});

test('users sensitive update retries with step-up token after backend requires confirmation', async () => {
  const harness = await openUsersStepUpHarness({
    updateResponses: [
      {
        status: 403,
        body: {
          error_code: 'step_up_required',
          message: 'Step-up verification required',
        },
      },
    ],
  });

  try {
    const licenseStatus = harness.page.getByRole('combobox', { name: 'License status' });
    await licenseStatus.focus();
    await harness.page.keyboard.press('ArrowDown');
    await harness.page.keyboard.press('ArrowDown');
    await harness.page.keyboard.press('Enter');
    await harness.page.getByLabel('Entitlements (comma or newline separated)').fill('dashboard:view, publish:run');
    await harness.page.getByRole('button', { name: 'Save changes' }).click();

    await harness.page.getByText('Confirm password: Save user changes').waitFor();
    await harness.page.getByText(
      'Confirm your password before saving sensitive user changes. The admin API will issue a short-lived step-up token for the protected update request.'
    ).waitFor();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'User changes saved. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.updateRequests.length, 2);
    assert.deepEqual(harness.calls.updateRequests[0].body, {
      license_status: 'revoked',
      entitlements: ['dashboard:view', 'publish:run'],
    });
    assert.equal(harness.calls.updateRequests[0].headers['x-step-up-token'], undefined);
    assert.equal(harness.calls.verifyBodies.length, 1);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'users.write',
    });
    assert.equal(harness.calls.updateRequests[1].headers['x-step-up-token'], 'admin_step_up_1');
    assert.deepEqual(harness.calls.updateRequests[1].body, {
      license_status: 'revoked',
      entitlements: ['dashboard:view', 'publish:run'],
    });
    await harness.page.getByText('publish:run').first().waitFor();
    await harness.page.getByText('Current state: revoked').waitFor();
  } finally {
    await harness.close();
  }
});

test('users update surfaces backend validation details inline without opening step-up', async () => {
  const harness = await openUsersStepUpHarness({
    updateResponses: [
      {
        status: 422,
        body: {
          detail: [
            {
              loc: ['body', 'license_expires_at'],
              msg: 'Input should be a valid datetime',
              type: 'datetime_parsing',
            },
          ],
        },
      },
    ],
  });

  try {
    await harness.page.getByLabel('License expiry (ISO-8601)').fill('not-a-date');
    await harness.page.getByRole('button', { name: 'Save changes' }).click();

    await harness.page.getByText('Please fix the highlighted user fields and retry.').waitFor();
    await harness.page.getByText('Input should be a valid datetime').waitFor();
    assert.equal(harness.calls.updateRequests.length, 1);
    assert.equal(harness.calls.verifyBodies.length, 0);
  } finally {
    await harness.close();
  }
});

test('users page opens a create-user modal with the minimal baseline fields', async () => {
  const harness = await openUsersStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Create user' }).first().click();
    const createDialog = harness.page.getByRole('dialog', { name: 'Create user' });
    await harness.page.getByText('Create a managed user with an initial password, baseline license state, and entitlements. The list and detail panel will refresh after a successful create.').waitFor();
    await createDialog.getByLabel('Username').waitFor();
    await createDialog.getByLabel('Initial password').waitFor();
    await createDialog.getByRole('combobox', { name: 'License status' }).waitFor();
  } finally {
    await harness.close();
  }
});

test('users create retries with step-up token and refreshes list/detail onto the new user', async () => {
  const harness = await openUsersStepUpHarness({
    createResponses: [
      {
        status: 403,
        body: {
          error_code: 'step_up_required',
          message: 'Step-up verification required',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Create user' }).first().click();
    const createDialog = harness.page.getByRole('dialog', { name: 'Create user' });
    await createDialog.getByLabel('Username').fill('alice2');
    await createDialog.getByLabel('Initial password').fill('TempSecret123!');
    await createDialog.getByLabel('Display name').fill('Alice 2');
    await createDialog.getByLabel('Email').fill('alice2@example.com');
    await createDialog.getByLabel('Tenant ID').fill('tenant_2');
    await createDialog.getByLabel('Entitlements (comma or newline separated)').fill('dashboard:view, publish:run');
    await createDialog.getByRole('button', { name: 'Create user' }).click();

    await harness.page.getByText('Confirm password: Create user').waitFor();
    await harness.page.getByText(
      'Confirm your password before creating a managed user. The admin API will issue a short-lived step-up token for the protected create request.'
    ).waitFor();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'User created. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.createRequests.length, 2);
    assert.deepEqual(harness.calls.createRequests[0].body, {
      username: 'alice2',
      password: 'TempSecret123!',
      display_name: 'Alice 2',
      email: 'alice2@example.com',
      tenant_id: 'tenant_2',
      license_status: 'active',
      entitlements: ['dashboard:view', 'publish:run'],
    });
    assert.equal(harness.calls.createRequests[0].headers.authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.createRequests[0].headers['x-step-up-token'], undefined);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'users.write',
    });
    assert.equal(harness.calls.createRequests[1].headers['x-step-up-token'], 'admin_step_up_1');
    await harness.page.getByText('alice2').first().waitFor();
    await harness.page.getByText('Alice 2').first().waitFor();
  } finally {
    await harness.close();
  }
});

test('users create surfaces backend 422 validation details in the modal form', async () => {
  const harness = await openUsersStepUpHarness({
    createResponses: [
      {
        status: 422,
        body: {
          detail: [
            {
              loc: ['body', 'username'],
              msg: 'Username already exists.',
              type: 'value_error',
            },
          ],
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Create user' }).first().click();
    const createDialog = harness.page.getByRole('dialog', { name: 'Create user' });
    await createDialog.getByLabel('Username').fill('alice');
    await createDialog.getByLabel('Initial password').fill('TempSecret123!');
    await createDialog.getByRole('button', { name: 'Create user' }).click();

    await harness.page.getByText('Username already exists.').waitFor();
    assert.equal(harness.calls.createRequests.length, 1);
    assert.equal(harness.calls.verifyBodies.length, 0);
  } finally {
    await harness.close();
  }
});

test('users create token expiry redirects back to login before opening step-up', async () => {
  const harness = await openUsersStepUpHarness({
    createResponses: [
      {
        status: 401,
        body: {
          error_code: 'token_expired',
          message: 'Session expired',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Create user' }).first().click();
    const createDialog = harness.page.getByRole('dialog', { name: 'Create user' });
    await createDialog.getByLabel('Username').fill('alice2');
    await createDialog.getByLabel('Initial password').fill('TempSecret123!');
    await createDialog.getByRole('button', { name: 'Create user' }).click();

    await harness.page.waitForURL(/#\/login$/);
    await harness.page.getByText('Your admin session expired. Please sign in again.').waitFor();
    assert.equal(harness.calls.createRequests.length, 1);
    assert.equal(harness.calls.verifyBodies.length, 0);
  } finally {
    await harness.close();
  }
});

test('devices page opens a password-confirmation modal before disable', async () => {
  const harness = await openDevicesStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Disable device' }).click();
    await harness.page.getByText('Confirm password: Disable device').waitFor();
    await harness.page.getByText(
      'Confirm your password before disabling this device. The admin API will issue a short-lived step-up token for the destructive request.'
    ).waitFor();
  } finally {
    await harness.close();
  }
});

test('devices step-up success submits verify request and forwards step-up token header', async () => {
  const harness = await openDevicesStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Disable device' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'Device disabled. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.verifyBodies.length, 1);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'devices.write',
    });
    assert.equal(harness.calls.verifyHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.disableHeaders.length, 1);
    assert.equal(harness.calls.disableHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.disableHeaders[0]['x-step-up-token'], 'admin_step_up_1');
    await harness.page.getByText('Current state: disabled').waitFor();
  } finally {
    await harness.close();
  }
});

test('devices step-up verification failure keeps modal open and blocks disable', async () => {
  const harness = await openDevicesStepUpHarness({
    verifyResponses: [
      {
        status: 401,
        body: {
          error_code: 'invalid_credentials',
          message: 'Invalid password',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Disable device' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('wrong-password');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText('Incorrect password. Please retry.').waitFor();
    await harness.page.getByText('Confirm password: Disable device').waitFor();
    assert.equal(harness.calls.disableHeaders.length, 0);
  } finally {
    await harness.close();
  }
});

test('devices step-up token expiry redirects back to login with auth notice', async () => {
  const harness = await openDevicesStepUpHarness({
    verifyResponses: [
      {
        status: 401,
        body: {
          error_code: 'token_expired',
          message: 'Session expired',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Disable device' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.waitForURL(/#\/login$/);
    await harness.page.getByText('Your admin session expired. Please sign in again.').waitFor();
    assert.equal(harness.calls.disableHeaders.length, 0);
  } finally {
    await harness.close();
  }
});

test('devices unbind step-up keeps the same verify flow while clearing binding state', async () => {
  const harness = await openDevicesStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Unbind device' }).click();
    await harness.page.getByText('Confirm password: Unbind device').waitFor();
    await harness.page.getByText(
      'Confirm your password before unbinding this device. The admin API will issue a short-lived step-up token for the destructive request.'
    ).waitFor();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'Device unbound. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.verifyBodies.length, 1);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'devices.write',
    });
    assert.equal(harness.calls.unbindHeaders.length, 1);
    assert.equal(harness.calls.unbindHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.unbindHeaders[0]['x-step-up-token'], 'admin_step_up_1');
    await harness.page.getByText('Current state: unbound').waitFor();
  } finally {
    await harness.close();
  }
});

test('devices rebind step-up submits payload diffs through the same tokenized path', async () => {
  const harness = await openDevicesStepUpHarness({
    initialDevice: UNBOUND_DEVICE,
  });

  try {
    await harness.page.locator('input[placeholder="u_1"]').last().fill('u_2');
    await harness.page.locator('input[placeholder="0.2.0"]').last().fill('0.3.0');
    await harness.page.getByRole('button', { name: 'Rebind device' }).click();
    await harness.page.getByText('Confirm password: Rebind device').waitFor();
    await harness.page.getByText(
      'Confirm your password before rebinding this device. The admin API will issue a short-lived step-up token for the destructive request.'
    ).waitFor();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'Device rebound. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.verifyBodies.length, 1);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'devices.write',
    });
    assert.equal(harness.calls.rebindRequests.length, 1);
    assert.equal(harness.calls.rebindRequests[0].headers.authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.rebindRequests[0].headers['x-step-up-token'], 'admin_step_up_1');
    assert.deepEqual(harness.calls.rebindRequests[0].body, {
      user_id: 'u_2',
      client_version: '0.3.0',
    });
    await harness.page.getByText('u_2').first().waitFor();
    await harness.page.getByText('Current state: bound').waitFor();
  } finally {
    await harness.close();
  }
});

test('sessions page opens a password-confirmation modal before revoke', async () => {
  const harness = await openSessionsStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Revoke session' }).click();
    await harness.page.getByText('Confirm password: Revoke session').waitFor();
    await harness.page.getByText(
      'Confirm your password before revoking this session. The admin API will issue a short-lived step-up token for the destructive request.'
    ).waitFor();
  } finally {
    await harness.close();
  }
});

test('sessions step-up success submits verify request and forwards step-up token header', async () => {
  const harness = await openSessionsStepUpHarness();

  try {
    await harness.page.getByRole('button', { name: 'Revoke session' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText(
      'Session revoked. The list and detail panel were refreshed from the backend.'
    ).waitFor();

    assert.equal(harness.calls.verifyBodies.length, 1);
    assert.deepEqual(harness.calls.verifyBodies[0], {
      password: 'admin-secret',
      scope: 'sessions.revoke',
    });
    assert.equal(harness.calls.verifyHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.revokeHeaders.length, 1);
    assert.equal(harness.calls.revokeHeaders[0].authorization, 'Bearer admin_access_token');
    assert.equal(harness.calls.revokeHeaders[0]['x-step-up-token'], 'admin_step_up_1');
    await harness.page.getByText('Current state: revoked:admin_revoke').waitFor();
  } finally {
    await harness.close();
  }
});

test('sessions step-up verification failure keeps modal open and blocks revoke', async () => {
  const harness = await openSessionsStepUpHarness({
    verifyResponses: [
      {
        status: 401,
        body: {
          error_code: 'invalid_credentials',
          message: 'Invalid password',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Revoke session' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('wrong-password');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.getByText('Incorrect password. Please retry.').waitFor();
    await harness.page.getByText('Confirm password: Revoke session').waitFor();
    assert.equal(harness.calls.revokeHeaders.length, 0);
  } finally {
    await harness.close();
  }
});

test('sessions step-up token expiry redirects back to login with auth notice', async () => {
  const harness = await openSessionsStepUpHarness({
    verifyResponses: [
      {
        status: 401,
        body: {
          error_code: 'token_expired',
          message: 'Session expired',
        },
      },
    ],
  });

  try {
    await harness.page.getByRole('button', { name: 'Revoke session' }).click();
    await harness.page.getByPlaceholder('Enter your password').fill('admin-secret');
    await harness.page.getByRole('button', { name: 'Confirm and continue' }).click();

    await harness.page.waitForURL(/#\/login$/);
    await harness.page.getByText('Your admin session expired. Please sign in again.').waitFor();
    assert.equal(harness.calls.revokeHeaders.length, 0);
  } finally {
    await harness.close();
  }
});

async function openUsersStepUpHarness(options = {}) {
  const browser = await launchChromium();
  const context = await browser.newContext();
  const page = await context.newPage();
  const calls = {
    verifyBodies: [],
    verifyHeaders: [],
    revokeHeaders: [],
    restoreHeaders: [],
    updateRequests: [],
    createRequests: [],
  };

  let managedUsers = (options.initialUsers ?? [options.initialUser ?? ACTIVE_USER]).map((user) => ({ ...user }));
  const verifyResponses = [...(options.verifyResponses ?? [])];
  const updateResponses = [...(options.updateResponses ?? [])];
  const createResponses = [...(options.createResponses ?? [])];

  await page.addInitScript((token) => {
    window.localStorage.setItem('remote_admin_access_token', token);
  }, 'admin_access_token');

  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (request.method() === 'GET' && url.pathname === '/admin/session') {
      await fulfillJson(route, ADMIN_SESSION);
      return;
    }

    if (request.method() === 'GET' && url.pathname === '/admin/users') {
      const filteredUsers = filterManagedUsers(managedUsers, url);
      const limit = Number(url.searchParams.get('limit') ?? '50');
      const offset = Number(url.searchParams.get('offset') ?? '0');
      const pagedUsers = filteredUsers.slice(offset, offset + limit);
      await fulfillJson(route, {
        items: pagedUsers.map((user) => ({ ...user })),
        total: filteredUsers.length,
        page: Math.floor(offset / Math.max(limit, 1)) + 1,
        page_size: limit,
      });
      return;
    }

    if (request.method() === 'GET' && url.pathname.startsWith('/admin/users/u_')) {
      const targetUser = managedUsers.find((user) => user.id === url.pathname.split('/').at(-1));
      await fulfillJson(route, targetUser ? { ...targetUser } : {
        error_code: 'not_found',
        message: 'User not found',
      }, targetUser ? 200 : 404);
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/step-up/password/verify') {
      calls.verifyHeaders.push(request.headers());
      calls.verifyBodies.push(JSON.parse(request.postData() ?? '{}'));
      const response = verifyResponses.shift() ?? {
        status: 200,
        body: {
          step_up_token: 'admin_step_up_1',
          scope: 'users.write',
          expires_at: '2026-05-01T00:05:00Z',
          method: 'password',
        },
      };
      await fulfillJson(route, response.body, response.status);
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/users/u_1/revoke') {
      calls.revokeHeaders.push(request.headers());
      managedUsers = managedUsers.map((user) =>
        user.id === 'u_1'
          ? {
              ...user,
              status: 'revoked',
              license_status: 'revoked',
            }
          : user
      );
      await fulfillJson(route, { success: true });
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/users/u_1/restore') {
      calls.restoreHeaders.push(request.headers());
      managedUsers = managedUsers.map((user) => (user.id === 'u_1' ? { ...ACTIVE_USER } : user));
      await fulfillJson(route, { success: true });
      return;
    }

    if (request.method() === 'PATCH' && url.pathname === '/admin/users/u_1') {
      const body = JSON.parse(request.postData() ?? '{}');
      calls.updateRequests.push({
        headers: request.headers(),
        body,
      });

      const response = updateResponses.shift();
      if (response) {
        await fulfillJson(route, response.body, response.status);
        return;
      }

      managedUsers = managedUsers.map((user) => {
        if (user.id !== 'u_1') {
          return user;
        }

        let nextUser = {
          ...user,
          ...body,
        };

        if (Object.hasOwn(body, 'display_name')) {
          nextUser = {
            ...nextUser,
            display_name: body.display_name,
          };
        }

        if (Object.hasOwn(body, 'license_expires_at')) {
          nextUser = {
            ...nextUser,
            license_expires_at: body.license_expires_at,
          };
        }

        if (body.license_status === 'revoked') {
          nextUser = {
            ...nextUser,
            status: 'revoked',
          };
        } else if (body.license_status === 'active') {
          nextUser = {
            ...nextUser,
            status: 'active',
          };
        }

        return nextUser;
      });

      await fulfillJson(route, { ...managedUsers.find((user) => user.id === 'u_1') });
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/users') {
      const body = JSON.parse(request.postData() ?? '{}');
      calls.createRequests.push({
        headers: request.headers(),
        body,
      });

      const response = createResponses.shift();
      if (response) {
        await fulfillJson(route, response.body, response.status);
        return;
      }

      const createdUser = {
        id: 'u_2',
        username: body.username,
        display_name: body.display_name ?? null,
        email: body.email ?? null,
        tenant_id: body.tenant_id ?? null,
        status: body.license_status === 'disabled' ? 'disabled' : 'active',
        license_status: body.license_status ?? 'active',
        license_expires_at: body.license_expires_at ?? null,
        entitlements: body.entitlements ?? [],
        device_count: 0,
        last_seen_at: null,
      };
      managedUsers = [createdUser, ...managedUsers.filter((user) => user.id !== createdUser.id)];
      await fulfillJson(route, createdUser);
      return;
    }

    await fulfillJson(
      route,
      {
        error_code: 'not_found',
        message: `Unhandled test route: ${request.method()} ${url.pathname}`,
      },
      404
    );
  });

  await page.goto(`${appBaseUrl}/index.html#/users`);
  await page.getByRole('heading', { name: 'Users' }).waitFor();
  await page.getByText('Alice').first().waitFor();
  await page.getByRole('button', { name: 'Revoke user' }).waitFor();

  return {
    page,
    calls,
    async close() {
      await context.close();
      await browser.close();
    },
  };
}

async function applyUsersStatusFilter(page, value) {
  const filterCard = page.locator('.ant-card').filter({ has: page.getByRole('button', { name: 'Apply filters' }) }).first();
  const statusSelector = filterCard.locator('.ant-form-item').filter({ hasText: 'Status' }).first().locator('.ant-select-selector');
  await statusSelector.click();
  await page.locator('.ant-select-dropdown:visible .ant-select-item-option-content').getByText(value, { exact: true }).click();
  await page.getByRole('button', { name: 'Apply filters' }).click();
}

function filterManagedUsers(users, url) {
  const query = (url.searchParams.get('q') ?? '').trim().toLowerCase();
  const status = (url.searchParams.get('status') ?? '').trim().toLowerCase();
  const licenseStatus = (url.searchParams.get('license_status') ?? '').trim().toLowerCase();

  return users.filter((user) => {
    if (status && String(user.status ?? '').toLowerCase() !== status) {
      return false;
    }
    if (licenseStatus && String(user.license_status ?? '').toLowerCase() !== licenseStatus) {
      return false;
    }
    if (!query) {
      return true;
    }

    const haystack = [user.id, user.username, user.display_name, user.email, user.tenant_id]
      .filter(Boolean)
      .map((entry) => String(entry).toLowerCase());
    return haystack.some((entry) => entry.includes(query));
  });
}

async function openDevicesStepUpHarness(options = {}) {
  const browser = await launchChromium();
  const context = await browser.newContext();
  const page = await context.newPage();
  const calls = {
    verifyBodies: [],
    verifyHeaders: [],
    unbindHeaders: [],
    disableHeaders: [],
    rebindRequests: [],
  };

  let currentDevice = { ...(options.initialDevice ?? ACTIVE_DEVICE) };
  const verifyResponses = [...(options.verifyResponses ?? [])];

  await page.addInitScript(({ storageKey, token }) => {
    window.localStorage.setItem(storageKey, token);
  }, { storageKey: ACCESS_TOKEN_KEY, token: 'admin_access_token' });

  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (request.method() === 'GET' && url.pathname === '/admin/session') {
      await fulfillJson(route, ADMIN_SESSION);
      return;
    }

    if (request.method() === 'GET' && url.pathname === '/admin/devices') {
      await fulfillJson(route, {
        items: [{ ...currentDevice }],
        total: 1,
        page: 1,
        page_size: 50,
      });
      return;
    }

    if (request.method() === 'GET' && url.pathname === '/admin/devices/device_1') {
      await fulfillJson(route, { ...currentDevice });
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/step-up/password/verify') {
      calls.verifyHeaders.push(request.headers());
      calls.verifyBodies.push(JSON.parse(request.postData() ?? '{}'));
      const response = verifyResponses.shift() ?? {
        status: 200,
        body: {
          step_up_token: 'admin_step_up_1',
          scope: 'devices.write',
          expires_at: '2026-05-01T00:05:00Z',
          method: 'password',
        },
      };
      await fulfillJson(route, response.body, response.status);
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/devices/device_1/disable') {
      calls.disableHeaders.push(request.headers());
      currentDevice = {
        ...currentDevice,
        device_status: 'disabled',
      };
      await fulfillJson(route, { success: true });
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/devices/device_1/unbind') {
      calls.unbindHeaders.push(request.headers());
      currentDevice = {
        ...currentDevice,
        user_id: null,
        device_status: 'unbound',
      };
      await fulfillJson(route, { success: true });
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/devices/device_1/rebind') {
      calls.rebindRequests.push({
        headers: request.headers(),
        body: JSON.parse(request.postData() ?? '{}'),
      });
      const payload = JSON.parse(request.postData() ?? '{}');
      currentDevice = {
        ...currentDevice,
        user_id: payload.user_id,
        client_version: payload.client_version,
        device_status: 'bound',
      };
      await fulfillJson(route, { success: true });
      return;
    }

    await fulfillJson(
      route,
      {
        error_code: 'not_found',
        message: `Unhandled test route: ${request.method()} ${url.pathname}`,
      },
      404
    );
  });

  await page.goto(`${appBaseUrl}/index.html#/devices`);
  await page.getByRole('heading', { name: 'Devices' }).waitFor();
  await page.getByText('device_1').first().waitFor();
  await page.getByRole('button', { name: 'Disable device' }).waitFor();

  return {
    page,
    calls,
    async close() {
      await context.close();
      await browser.close();
    },
  };
}

async function openSessionsStepUpHarness(options = {}) {
  const browser = await launchChromium();
  const context = await browser.newContext();
  const page = await context.newPage();
  const calls = {
    verifyBodies: [],
    verifyHeaders: [],
    revokeHeaders: [],
  };

  let currentSession = { ...ACTIVE_SESSION };
  const verifyResponses = [...(options.verifyResponses ?? [])];

  await page.addInitScript(({ storageKey, token }) => {
    window.localStorage.setItem(storageKey, token);
  }, { storageKey: ACCESS_TOKEN_KEY, token: 'admin_access_token' });

  await page.route(`${API_BASE}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (request.method() === 'GET' && url.pathname === '/admin/session') {
      await fulfillJson(route, ADMIN_SESSION);
      return;
    }

    if (request.method() === 'GET' && url.pathname === '/admin/sessions') {
      await fulfillJson(route, {
        items: [{ ...currentSession }],
        total: 1,
        page: 1,
        page_size: 50,
      });
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/step-up/password/verify') {
      calls.verifyHeaders.push(request.headers());
      calls.verifyBodies.push(JSON.parse(request.postData() ?? '{}'));
      const response = verifyResponses.shift() ?? {
        status: 200,
        body: {
          step_up_token: 'admin_step_up_1',
          scope: 'sessions.revoke',
          expires_at: '2026-05-01T00:05:00Z',
          method: 'password',
        },
      };
      await fulfillJson(route, response.body, response.status);
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/sessions/sess_1/revoke') {
      calls.revokeHeaders.push(request.headers());
      currentSession = {
        ...currentSession,
        auth_state: 'revoked:admin_revoke',
      };
      await fulfillJson(route, { success: true });
      return;
    }

    await fulfillJson(
      route,
      {
        error_code: 'not_found',
        message: `Unhandled test route: ${request.method()} ${url.pathname}`,
      },
      404
    );
  });

  await page.goto(`${appBaseUrl}/index.html#/sessions`);
  await page.getByRole('heading', { name: 'Sessions' }).waitFor();
  await page.getByText('sess_1').first().waitFor();
  await page.getByRole('button', { name: 'Revoke session' }).waitFor();

  return {
    page,
    calls,
    async close() {
      await context.close();
      await browser.close();
    },
  };
}

async function startStaticServer(rootDir) {
  const normalizedRootDir = normalize(rootDir);
  const server = http.createServer(async (request, response) => {
    const requestUrl = new URL(request.url ?? '/', 'http://127.0.0.1');
    const pathname = requestUrl.pathname === '/' ? '/index.html' : requestUrl.pathname;
    const filePath = normalize(join(normalizedRootDir, pathname.replace(/^\/+/, '')));

    if (!filePath.startsWith(normalizedRootDir)) {
      response.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Forbidden');
      return;
    }

    try {
      const content = await readFile(filePath);
      response.writeHead(200, {
        'Content-Type': CONTENT_TYPES[extname(filePath)] ?? 'application/octet-stream',
      });
      response.end(content);
    } catch {
      response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      response.end('Not found');
    }
  });

  await new Promise((resolve) => {
    server.listen(0, '127.0.0.1', resolve);
  });

  const address = server.address();
  if (!address || typeof address === 'string') {
    throw new Error('Unable to determine static server address');
  }

  return {
    server,
    baseUrl: `http://127.0.0.1:${address.port}`,
  };
}

async function launchChromium() {
  const launchOptions = [
    { headless: true },
    { headless: true, channel: 'msedge' },
    { headless: true, channel: 'chrome' },
  ];

  let lastError;
  for (const options of launchOptions) {
    try {
      return await chromium.launch(options);
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError;
}

async function fulfillJson(route, body, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json; charset=utf-8',
    body: JSON.stringify(body),
  });
}
