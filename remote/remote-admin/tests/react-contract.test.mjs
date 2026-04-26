import test from 'node:test';
import assert from 'node:assert/strict';

import {
  ADMIN_STEP_UP_SCOPE_USERS_WRITE,
  buildAuditLogQuery,
  buildDevicesQuery,
  buildSessionsQuery,
  buildUsersQuery,
  canEditUsersRole,
  createAdminAuthHeaders,
  formatPageSummary,
  hasNextPage,
  hasPreviousPage,
  mapAdminActionError,
  mapDeviceActionError,
  mapLoginError,
  mapSessionActionError,
  mapStepUpVerifyError,
  replacePaginationPageSize,
  revokeAdminUser,
  shiftOffsetPagination,
  toUtcAuditFilterTimestamp,
  updateAdminUser,
  verifyAdminStepUpPassword,
} from '../dist/features/auth/auth-client.js';
import {
  getAdminPageTitle,
  resolveProtectedAdminRedirect,
  resolveRootAdminPath,
} from '../dist/routes/route-helpers.js';

const session = {
  session_id: 'admin_sess_123',
  expires_at: '2026-04-30T00:00:00Z',
  user: {
    id: 'admin_1',
    username: 'admin',
    display_name: 'Remote Admin',
    role: 'super_admin',
  },
};

const readonlySession = {
  ...session,
  user: {
    ...session.user,
    role: 'support_readonly',
  },
};

const users = [
  {
    id: 'u_1',
    username: 'alice',
    display_name: 'Alice',
    email: 'alice@example.com',
    tenant_id: 'tenant_1',
    status: 'active',
    license_status: 'active',
    license_expires_at: '2026-07-01T00:00:00Z',
    entitlements: ['dashboard:view', 'publish:run'],
    device_count: 1,
    last_seen_at: '2026-04-30T00:00:00Z',
  },
];

test('root redirect helper preserves login/dashboard contract', () => {
  assert.equal(resolveRootAdminPath('authenticated'), '/dashboard');
  assert.equal(resolveRootAdminPath('anonymous'), '/login');
});

test('protected route helper keeps auth redirect contract stable', () => {
  assert.equal(resolveProtectedAdminRedirect('anonymous', '/users'), '/login');
  assert.equal(resolveProtectedAdminRedirect('anonymous', '/login'), null);
  assert.equal(resolveProtectedAdminRedirect('authenticated', '/login'), '/dashboard');
  assert.equal(resolveProtectedAdminRedirect('authenticated', '/users'), null);
  assert.equal(resolveProtectedAdminRedirect('restoring', '/users'), null);
});

test('page title helper maps known routes and falls back safely', () => {
  assert.equal(getAdminPageTitle('/dashboard'), 'Dashboard');
  assert.equal(getAdminPageTitle('/audit-logs'), 'Audit logs');
  assert.equal(getAdminPageTitle('/unknown'), 'Remote Admin');
});

test('login error mapping keeps admin UX stable', () => {
  assert.equal(mapLoginError('invalid_credentials'), 'Incorrect username or password.');
  assert.equal(mapLoginError('too_many_requests'), 'Too many attempts. Please retry later.');
  assert.equal(mapLoginError('forbidden'), 'This admin account is not allowed to sign in.');
  assert.equal(mapLoginError(), 'Unable to sign in right now.');
});

test('role gating keeps write access rules stable', () => {
  assert.equal(canEditUsersRole(session), true);
  assert.equal(canEditUsersRole(readonlySession), false);
});

test('admin action error mapping keeps authorization UX stable', () => {
  assert.equal(mapAdminActionError('forbidden'), 'Your current role is read-only and cannot perform this action.');
  assert.equal(mapAdminActionError('not_found'), 'The requested user could not be found.');
  assert.equal(mapAdminActionError('step_up_required'), 'Please confirm your password before retrying this action.');
  assert.equal(
    mapAdminActionError('token_expired'),
    'Your admin session expired. Please sign in again.'
  );
});

test('device action error mapping keeps device UX stable', () => {
  assert.equal(mapDeviceActionError('forbidden'), 'Your current role is read-only and cannot perform this device action.');
  assert.equal(mapDeviceActionError('not_found'), 'The requested device or target user could not be found.');
  assert.equal(mapDeviceActionError('step_up_invalid'), 'Your confirmation expired or is no longer valid. Please confirm again.');
});

test('session action error mapping keeps session UX stable', () => {
  assert.equal(mapSessionActionError('forbidden'), 'Your current role is read-only and cannot revoke sessions.');
  assert.equal(mapSessionActionError('not_found'), 'The requested session could not be found.');
  assert.equal(mapSessionActionError('step_up_expired'), 'Your confirmation expired. Please confirm your password again.');
});

test('step-up verification error mapping keeps password-confirmation UX stable', () => {
  assert.equal(mapStepUpVerifyError('invalid_credentials'), 'Incorrect password. Please retry.');
  assert.equal(mapStepUpVerifyError('too_many_requests'), 'Too many confirmation attempts. Please retry later.');
  assert.equal(mapStepUpVerifyError('forbidden'), 'Your current role cannot perform this action.');
  assert.equal(mapStepUpVerifyError('token_expired'), 'Your admin session expired. Please sign in again.');
});

test('audit query builder keeps filter ordering and UTC boundaries stable', () => {
  const query = buildAuditLogQuery({
    eventType: 'authorization_user_revoked',
    actorId: 'admin_1',
    targetUserId: 'u_1',
    targetDeviceId: 'device_1',
    targetSessionId: 'sess_1',
    createdFrom: '2026-04-01T00:00',
    createdTo: '2026-04-30T23:59',
    limit: 50,
    offset: 100,
  });

  assert.deepEqual(
    query
      .slice(1)
      .split('&')
      .map((entry) => entry.split('=')[0]),
    [
      'event_type',
      'actor_id',
      'target_user_id',
      'target_device_id',
      'target_session_id',
      'created_from',
      'created_to',
      'limit',
      'offset',
    ]
  );

  const createdFrom = toUtcAuditFilterTimestamp('2026-04-01T00:00', 'start');
  const createdTo = toUtcAuditFilterTimestamp('2026-04-30T23:59', 'end');
  assert.ok(createdFrom.endsWith('Z'));
  assert.ok(createdTo.endsWith('Z'));
  assert.equal(new Date(createdFrom).getUTCSeconds(), 0);
  assert.equal(new Date(createdFrom).getUTCMilliseconds(), 0);
  assert.equal(new Date(createdTo).getUTCSeconds(), 59);
  assert.equal(new Date(createdTo).getUTCMilliseconds(), 999);
});

test('list query helpers include stable limit and offset parameters', () => {
  assert.equal(
    buildUsersQuery({ query: 'alice', status: 'active', licenseStatus: 'revoked', limit: 25, offset: 50 }),
    '?q=alice&status=active&license_status=revoked&limit=25&offset=50'
  );
  assert.equal(
    buildDevicesQuery({ query: 'device_1', status: 'disabled', userId: 'u_1', limit: 10, offset: 20 }),
    '?q=device_1&device_status=disabled&user_id=u_1&limit=10&offset=20'
  );
  assert.equal(
    buildSessionsQuery({
      query: 'sess_1',
      authState: 'authenticated_active',
      userId: 'u_1',
      deviceId: 'device_1',
      limit: 50,
      offset: 100,
    }),
    '?q=sess_1&auth_state=authenticated_active&user_id=u_1&device_id=device_1&limit=50&offset=100'
  );
});

test('createAdminAuthHeaders appends optional step-up token without changing bearer auth', () => {
  assert.deepEqual(createAdminAuthHeaders('admin_access_token'), {
    Authorization: 'Bearer admin_access_token',
  });
  assert.deepEqual(createAdminAuthHeaders('admin_access_token', { contentType: true, stepUpToken: 'step_up_1' }), {
    Authorization: 'Bearer admin_access_token',
    'Content-Type': 'application/json',
    'X-Step-Up-Token': 'step_up_1',
  });
});

test('step-up verify client posts password confirmation contract to backend', async () => {
  const originalWindow = globalThis.window;
  const originalFetch = globalThis.fetch;
  let requestInput;
  let requestInit;
  globalThis.window = { location: { search: '' } };
  globalThis.fetch = async (input, init) => {
    requestInput = input;
    requestInit = init;
    return new Response(
      JSON.stringify({
        step_up_token: 'admin_step_up_1',
        scope: ADMIN_STEP_UP_SCOPE_USERS_WRITE,
        expires_at: '2026-05-01T00:05:00Z',
        method: 'password',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  };

  try {
    const response = await verifyAdminStepUpPassword(
      'admin_access_token',
      'admin-secret',
      ADMIN_STEP_UP_SCOPE_USERS_WRITE
    );

    assert.equal(response.step_up_token, 'admin_step_up_1');
    assert.equal(String(requestInput), 'http://127.0.0.1:8100/admin/step-up/password/verify');
    assert.equal(requestInit.method, 'POST');
    assert.deepEqual(requestInit.headers, {
      Authorization: 'Bearer admin_access_token',
      'Content-Type': 'application/json',
    });
    assert.equal(
      requestInit.body,
      JSON.stringify({
        password: 'admin-secret',
        scope: ADMIN_STEP_UP_SCOPE_USERS_WRITE,
      })
    );
  } finally {
    globalThis.window = originalWindow;
    globalThis.fetch = originalFetch;
  }
});

test('destructive admin client forwards X-Step-Up-Token header', async () => {
  const originalWindow = globalThis.window;
  const originalFetch = globalThis.fetch;
  let requestInit;
  globalThis.window = { location: { search: '' } };
  globalThis.fetch = async (_input, init) => {
    requestInit = init;
    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };

  try {
    const response = await revokeAdminUser('admin_access_token', 'u_1', 'step_up_1');
    assert.equal(response.success, true);
    assert.deepEqual(requestInit.headers, {
      Authorization: 'Bearer admin_access_token',
      'X-Step-Up-Token': 'step_up_1',
    });
  } finally {
    globalThis.window = originalWindow;
    globalThis.fetch = originalFetch;
  }
});

test('update admin user client posts PATCH payload and optional step-up header', async () => {
  const originalWindow = globalThis.window;
  const originalFetch = globalThis.fetch;
  let requestInput;
  let requestInit;
  globalThis.window = { location: { search: '' } };
  globalThis.fetch = async (input, init) => {
    requestInput = input;
    requestInit = init;
    return new Response(
      JSON.stringify({
        id: 'u_1',
        username: 'alice',
        display_name: 'Alice Updated',
        email: 'alice@example.com',
        tenant_id: 'tenant_1',
        status: 'active',
        license_status: 'active',
        license_expires_at: '2026-07-01T00:00:00Z',
        entitlements: ['dashboard:view'],
        device_count: 1,
        last_seen_at: '2026-04-30T00:00:00Z',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  };

  try {
    const response = await updateAdminUser(
      'admin_access_token',
      'u_1',
      {
        display_name: 'Alice Updated',
        entitlements: ['dashboard:view'],
      },
      'step_up_1'
    );
    assert.equal(response.display_name, 'Alice Updated');
    assert.equal(String(requestInput), 'http://127.0.0.1:8100/admin/users/u_1');
    assert.equal(requestInit.method, 'PATCH');
    assert.deepEqual(requestInit.headers, {
      Authorization: 'Bearer admin_access_token',
      'Content-Type': 'application/json',
      'X-Step-Up-Token': 'step_up_1',
    });
    assert.equal(
      requestInit.body,
      JSON.stringify({
        display_name: 'Alice Updated',
        entitlements: ['dashboard:view'],
      })
    );
  } finally {
    globalThis.window = originalWindow;
    globalThis.fetch = originalFetch;
  }
});

test('formatPageSummary keeps paginated list copy consistent across admin resources', () => {
  assert.equal(
    formatPageSummary({ items: users, total: 12, page: 2, page_size: 10 }),
    'Page 2 · page size 10 · total 12'
  );
});

test('offset pagination helpers keep page navigation state consistent', () => {
  assert.equal(hasPreviousPage({ limit: 25, offset: 0 }), false);
  assert.equal(hasPreviousPage({ limit: 25, offset: 25 }), true);
  assert.equal(hasNextPage({ items: users, total: 26, page: 1, page_size: 25 }, { limit: 25, offset: 0 }), true);
  assert.equal(hasNextPage({ items: users, total: 1, page: 1, page_size: 25 }, { limit: 25, offset: 0 }), false);
  assert.deepEqual(shiftOffsetPagination({ limit: 25, offset: 25 }, 'prev'), { limit: 25, offset: 0 });
  assert.deepEqual(shiftOffsetPagination({ limit: 25, offset: 25 }, 'next'), { limit: 25, offset: 50 });
  assert.deepEqual(replacePaginationPageSize({ limit: 25, offset: 75 }, 50), { limit: 50, offset: 0 });
});
