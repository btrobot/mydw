import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildAuditLogQuery,
  buildDevicesQuery,
  buildSessionsQuery,
  buildUsersQuery,
  canEditUsers,
  createDeviceEditor,
  createInitialState,
  createUserEditor,
  mapAdminActionError,
  mapDeviceActionError,
  mapLoginError,
  mapSessionActionError,
  renderApp,
  resolveGuardedRoute,
} from '../dist/app/App.js';
import {
  ADMIN_STEP_UP_SCOPE_USERS_WRITE,
  buildAuditLogQuery as buildReactAuditLogQuery,
  buildDevicesQuery as buildReactDevicesQuery,
  buildSessionsQuery as buildReactSessionsQuery,
  buildUsersQuery as buildReactUsersQuery,
  createAdminAuthHeaders,
  formatPageSummary,
  hasNextPage,
  hasPreviousPage,
  mapStepUpVerifyError,
  replacePaginationPageSize,
  revokeAdminUser,
  shiftOffsetPagination,
  toUtcAuditFilterTimestamp,
  verifyAdminStepUpPassword,
} from '../dist/features/auth/auth-client.js';

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

const devices = [
  {
    device_id: 'device_1',
    user_id: 'u_1',
    device_status: 'bound',
    first_bound_at: '2026-04-01T00:00:00Z',
    last_seen_at: '2026-04-30T00:00:00Z',
    client_version: '0.2.0',
  },
];

const sessions = [
  {
    session_id: 'sess_1',
    user_id: 'u_1',
    device_id: 'device_1',
    auth_state: 'authenticated_active',
    issued_at: '2026-04-01T00:00:00Z',
    expires_at: '2026-04-30T00:00:00Z',
    last_seen_at: '2026-04-29T00:00:00Z',
  },
];

const auditLogs = [
  {
    id: '1',
    event_type: 'authorization_user_revoked',
    actor_type: 'admin',
    actor_id: 'admin_1',
    target_user_id: 'u_1',
    target_device_id: null,
    target_session_id: null,
    request_id: 'req-1',
    trace_id: 'trace-1',
    created_at: '2026-04-30T00:00:00Z',
    details: { reason: 'authorization_revoked', changed_fields: { license_status: 'revoked' } },
  },
  {
    id: '2',
    event_type: 'auth_login_failed',
    actor_type: 'end_user',
    actor_id: 'alice',
    target_user_id: 'u_1',
    target_device_id: 'device_1',
    target_session_id: null,
    request_id: 'req-2',
    trace_id: 'trace-2',
    created_at: '2026-04-30T01:00:00Z',
    details: { reason: 'invalid_credentials' },
  },
];

test('unauthenticated protected routes redirect to login', () => {
  assert.deepEqual(resolveGuardedRoute('dashboard', false), { route: 'login', redirectTo: '#/login' });
  assert.deepEqual(resolveGuardedRoute('users', false), { route: 'login', redirectTo: '#/login' });
});

test('authenticated login route redirects to dashboard', () => {
  assert.deepEqual(resolveGuardedRoute('login', true), { route: 'dashboard', redirectTo: '#/dashboard' });
});

test('login error mapping keeps admin UX stable', () => {
  assert.equal(mapLoginError('invalid_credentials'), 'Incorrect username or password.');
  assert.equal(mapLoginError('too_many_requests'), 'Too many attempts. Please retry later.');
  assert.equal(mapLoginError('forbidden'), 'This admin account is not allowed to sign in.');
});

test('dashboard placeholder renders authenticated shell content', () => {
  const state = createInitialState('dashboard');
  state.session = session;
  state.status = 'ready';
  state.dashboardMetrics.activeSessions = 3;
  state.dashboardMetrics.loginFailures = 2;
  state.dashboardMetrics.deviceMismatches = 1;
  state.dashboardMetrics.destructiveActions = 4;
  state.dashboardMetrics.generatedAt = '2026-04-30T02:00:00Z';
  state.dashboardMetrics.recentFailures = [auditLogs[1]];
  state.dashboardMetrics.recentDestructiveActions = [auditLogs[0]];
  const html = renderApp(state);
  assert.match(html, /Remote Admin/);
  assert.match(html, /Recent critical events/);
  assert.match(html, /Operator follow-up queue/);
  assert.match(html, /admin_sess_123/);
  assert.match(html, /Destructive actions/);
  assert.match(html, /#\/audit-logs/);
  assert.match(html, /auth_login_failed/);
});

test('dashboard error renders retry affordance', () => {
  const state = createInitialState('dashboard');
  state.session = session;
  state.status = 'ready';
  state.dashboardMetrics.errorMessage = 'Failed to load dashboard metrics.';
  const html = renderApp(state);
  assert.match(html, /dashboard-retry/);
  assert.match(html, /Retry/);
});

test('users page renders real user control layout', () => {
  const state = createInitialState('users');
  state.session = session;
  state.status = 'ready';
  state.usersPage.items = users;
  state.usersPage.selectedUserId = 'u_1';
  state.usersPage.detail = users[0];
  state.usersPage.editor = createUserEditor(users[0]);
  const html = renderApp(state);
  assert.match(html, /Users/);
  assert.match(html, /Alice/);
  assert.match(html, /Apply filters/);
  assert.match(html, /All licenses/);
  assert.match(html, /Entitlements:/);
  assert.match(html, /Revoke user/);
  assert.match(html, /Restore user/);
});

test('users and devices render retryable detail errors', () => {
  const usersState = createInitialState('users');
  usersState.session = session;
  usersState.status = 'ready';
  usersState.usersPage.items = users;
  usersState.usersPage.selectedUserId = 'u_1';
  usersState.usersPage.detailErrorMessage = 'Failed to load the selected user.';
  let html = renderApp(usersState);
  assert.match(html, /user-detail-retry/);

  const devicesState = createInitialState('devices');
  devicesState.session = session;
  devicesState.status = 'ready';
  devicesState.devicesPage.items = devices;
  devicesState.devicesPage.selectedDeviceId = 'device_1';
  devicesState.devicesPage.detailErrorMessage = 'Failed to load the selected device.';
  html = renderApp(devicesState);
  assert.match(html, /device-detail-retry/);
});

test('readonly role disables destructive controls', () => {
  const state = createInitialState('users');
  state.session = readonlySession;
  state.status = 'ready';
  state.usersPage.items = users;
  state.usersPage.selectedUserId = 'u_1';
  state.usersPage.detail = users[0];
  state.usersPage.editor = createUserEditor(users[0]);
  const html = renderApp(state);
  assert.equal(canEditUsers(readonlySession), false);
  assert.match(html, /read-only/);
  assert.match(html, /disabled/);
});

test('admin action error mapping keeps authorization UX stable', () => {
  assert.equal(mapAdminActionError('forbidden'), 'Your current role is read-only and cannot perform this action.');
  assert.equal(mapAdminActionError('not_found'), 'The requested user could not be found.');
});

test('device action error mapping keeps device UX stable', () => {
  assert.equal(mapDeviceActionError('forbidden'), 'Your current role is read-only and cannot perform this device action.');
  assert.equal(mapDeviceActionError('not_found'), 'The requested device could not be found.');
});

test('sessions page renders session control layout', () => {
  const state = createInitialState('sessions');
  state.session = session;
  state.status = 'ready';
  state.sessionsPage.items = sessions;
  state.sessionsPage.selectedSessionId = 'sess_1';
  state.sessionsPage.actionInFlightId = 'sess_1';
  const html = renderApp(state);
  assert.match(html, /Sessions/);
  assert.match(html, /sess_1/);
  assert.match(html, /Apply filters/);
  assert.match(html, /Session detail/);
  assert.match(html, /authenticated_active/);
  assert.match(html, /Issued at/);
  assert.match(html, /Revoking session.../);
});

test('session action error mapping keeps session UX stable', () => {
  assert.equal(mapSessionActionError('forbidden'), 'Your current role is read-only and cannot revoke sessions.');
  assert.equal(mapSessionActionError('not_found'), 'The requested session could not be found.');
});

test('step-up verification error mapping keeps password-confirmation UX stable', () => {
  assert.equal(mapStepUpVerifyError('invalid_credentials'), 'Incorrect password. Please retry.');
  assert.equal(mapStepUpVerifyError('too_many_requests'), 'Too many confirmation attempts. Please retry later.');
  assert.equal(mapStepUpVerifyError('forbidden'), 'Your current role cannot perform this action.');
});

test('devices page renders device control layout', () => {
  const state = createInitialState('devices');
  state.session = session;
  state.status = 'ready';
  state.devicesPage.items = devices;
  state.devicesPage.selectedDeviceId = 'device_1';
  state.devicesPage.detail = devices[0];
  state.devicesPage.editor = createDeviceEditor(devices[0]);
  const html = renderApp(state);
  assert.match(html, /Devices/);
  assert.match(html, /device_1/);
  assert.match(html, /Bound user/);
  assert.match(html, /Apply filters/);
  assert.match(html, /Unbind device/);
  assert.match(html, /Disable device/);
  assert.match(html, /Rebind device/);
});

test('audit page renders audit log list layout', () => {
  const state = createInitialState('audit-logs');
  state.session = session;
  state.status = 'ready';
  state.auditPage.items = auditLogs;
  state.auditPage.total = auditLogs.length;
  state.auditPage.selectedAuditId = '1';
  state.auditPage.filters.eventType = 'authorization_user_revoked';
  state.auditPage.filters.actorId = 'admin_1';
  state.auditPage.filters.targetUserId = 'u_1';
  state.auditPage.filters.targetDeviceId = 'device_1';
  state.auditPage.filters.targetSessionId = 'sess_1';
  state.auditPage.filters.createdFrom = '2026-04-01T00:00';
  state.auditPage.filters.createdTo = '2026-04-30T23:59';
  const html = renderApp(state);
  assert.match(html, /Audit logs/);
  assert.match(html, /authorization_user_revoked/);
  assert.match(html, /Refresh audit logs/);
  assert.match(html, /Clear filters/);
  assert.match(html, /Previous page/);
  assert.match(html, /Target session/);
  assert.match(html, /Request ID:/);
  assert.match(html, /trace-1/);
  assert.match(html, /changed_fields/);
});

test('buildAuditLogQuery keeps filter ordering stable', () => {
  const query = buildAuditLogQuery({
    eventType: 'authorization_user_revoked',
    actorId: 'admin_1',
    targetUserId: 'u_1',
    targetDeviceId: 'device_1',
    targetSessionId: 'sess_1',
    createdFrom: '2026-04-01T00:00',
    createdTo: '2026-04-30T23:59',
    limit: 25,
    offset: 50,
  });

  const params = new URLSearchParams(query.slice(1));
  const createdFrom = params.get('created_from');
  const createdTo = params.get('created_to');

  assert.equal(params.get('event_type'), 'authorization_user_revoked');
  assert.equal(params.get('actor_id'), 'admin_1');
  assert.equal(params.get('target_user_id'), 'u_1');
  assert.equal(params.get('target_device_id'), 'device_1');
  assert.equal(params.get('target_session_id'), 'sess_1');
  assert.equal(params.get('limit'), '25');
  assert.equal(params.get('offset'), '50');
  assert.ok(createdFrom?.endsWith('Z'));
  assert.ok(createdTo?.endsWith('Z'));
  assert.equal(new Date(createdFrom).getUTCSeconds(), 0);
  assert.equal(new Date(createdFrom).getUTCMilliseconds(), 0);
  assert.equal(new Date(createdTo).getUTCSeconds(), 59);
  assert.equal(new Date(createdTo).getUTCMilliseconds(), 999);
});

test('React audit query helpers keep UTC conversion and ordering aligned with legacy audit route', () => {
  const query = buildReactAuditLogQuery({
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

test('buildUsersQuery, buildDevicesQuery, and buildSessionsQuery encode filter state', () => {
  assert.equal(buildUsersQuery({ query: 'alice', status: 'active', licenseStatus: 'revoked' }), '?q=alice&status=active&license_status=revoked');
  assert.equal(buildDevicesQuery({ query: 'device_1', status: 'disabled', userId: 'u_1' }), '?q=device_1&device_status=disabled&user_id=u_1');
  assert.equal(buildSessionsQuery({ query: 'sess_1', authState: 'authenticated_active', userId: 'u_1', deviceId: 'device_1' }), '?q=sess_1&auth_state=authenticated_active&user_id=u_1&device_id=device_1');
});

test('React list query helpers include stable limit and offset parameters', () => {
  assert.equal(
    buildReactUsersQuery({ query: 'alice', status: 'active', licenseStatus: 'revoked', limit: 25, offset: 50 }),
    '?q=alice&status=active&license_status=revoked&limit=25&offset=50'
  );
  assert.equal(
    buildReactDevicesQuery({ query: 'device_1', status: 'disabled', userId: 'u_1', limit: 10, offset: 20 }),
    '?q=device_1&device_status=disabled&user_id=u_1&limit=10&offset=20'
  );
  assert.equal(
    buildReactSessionsQuery({
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

test('audit page renders empty and loading operational states', () => {
  const state = createInitialState('audit-logs');
  state.session = session;
  state.status = 'ready';
  state.auditPage.loading = true;
  let html = renderApp(state);
  assert.match(html, /Loading audit logs/);

  state.auditPage.loading = false;
  html = renderApp(state);
  assert.match(html, /No audit events matched the current filters/);
});

test('users, devices, and sessions render retryable collection errors without empty-state conflicts', () => {
  const usersState = createInitialState('users');
  usersState.session = session;
  usersState.status = 'ready';
  usersState.usersPage.errorMessage = 'Failed to load admin users.';
  let html = renderApp(usersState);
  assert.match(html, /users-retry/);
  assert.doesNotMatch(html, /No managed users matched the current filters/);

  const devicesState = createInitialState('devices');
  devicesState.session = session;
  devicesState.status = 'ready';
  devicesState.devicesPage.errorMessage = 'Failed to load devices.';
  html = renderApp(devicesState);
  assert.match(html, /devices-retry/);
  assert.doesNotMatch(html, /No devices matched the current filters/);

  const sessionsState = createInitialState('sessions');
  sessionsState.session = session;
  sessionsState.status = 'ready';
  sessionsState.sessionsPage.errorMessage = 'Failed to load sessions.';
  html = renderApp(sessionsState);
  assert.match(html, /sessions-retry/);
  assert.doesNotMatch(html, /No sessions matched the current filters/);

  const auditState = createInitialState('audit-logs');
  auditState.session = session;
  auditState.status = 'ready';
  auditState.auditPage.errorMessage = 'Failed to load audit logs.';
  html = renderApp(auditState);
  assert.match(html, /audit-retry/);
  assert.doesNotMatch(html, /No audit events matched the current filters/);
});

test('users, devices, sessions, and audit keep empty states for true empty results', () => {
  const usersState = createInitialState('users');
  usersState.session = session;
  usersState.status = 'ready';
  let html = renderApp(usersState);
  assert.match(html, /No managed users matched the current filters/);

  const devicesState = createInitialState('devices');
  devicesState.session = session;
  devicesState.status = 'ready';
  html = renderApp(devicesState);
  assert.match(html, /No devices matched the current filters/);

  const sessionsState = createInitialState('sessions');
  sessionsState.session = session;
  sessionsState.status = 'ready';
  html = renderApp(sessionsState);
  assert.match(html, /No sessions matched the current filters/);

  const auditState = createInitialState('audit-logs');
  auditState.session = session;
  auditState.status = 'ready';
  html = renderApp(auditState);
  assert.match(html, /No audit events matched the current filters/);
});
