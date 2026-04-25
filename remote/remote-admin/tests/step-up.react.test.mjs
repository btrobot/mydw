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

async function openUsersStepUpHarness(options = {}) {
  const browser = await launchChromium();
  const context = await browser.newContext();
  const page = await context.newPage();
  const calls = {
    verifyBodies: [],
    verifyHeaders: [],
    revokeHeaders: [],
  };

  let currentUser = { ...ACTIVE_USER };
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

    await fulfillJson(
      route,
      {
        error_code: 'not_found',
        message: `Unhandled test route: ${request.method()} ${url.pathname}`,
      },
      404
    );
  });

  await page.goto(`${appBaseUrl}/react-index.html#/users`);
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

async function startStaticServer(rootDir) {
  const normalizedRootDir = normalize(rootDir);
  const server = http.createServer(async (request, response) => {
    const requestUrl = new URL(request.url ?? '/', 'http://127.0.0.1');
    const pathname = requestUrl.pathname === '/' ? '/react-index.html' : requestUrl.pathname;
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
