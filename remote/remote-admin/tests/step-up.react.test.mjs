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
  };

  let currentUser = { ...(options.initialUser ?? ACTIVE_USER) };
  const verifyResponses = [...(options.verifyResponses ?? [])];

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
      await fulfillJson(route, {
        items: [{ ...currentUser }],
        total: 1,
        page: 1,
        page_size: 50,
      });
      return;
    }

    if (request.method() === 'GET' && url.pathname === '/admin/users/u_1') {
      await fulfillJson(route, { ...currentUser });
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
      currentUser = {
        ...currentUser,
        status: 'revoked',
        license_status: 'revoked',
      };
      await fulfillJson(route, { success: true });
      return;
    }

    if (request.method() === 'POST' && url.pathname === '/admin/users/u_1/restore') {
      calls.restoreHeaders.push(request.headers());
      currentUser = {
        ...ACTIVE_USER,
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
