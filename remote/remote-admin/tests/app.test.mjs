import test from 'node:test';
import assert from 'node:assert/strict';

import {
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
    actor_id: 'admin_1',
    target_user_id: 'u_1',
    target_device_id: null,
    target_session_id: null,
    created_at: '2026-04-30T00:00:00Z',
    details: { reason: 'authorization_revoked' },
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
  const html = renderApp(state);
  assert.match(html, /Remote Admin/);
  assert.match(html, /Dashboard operations snapshot/);
  assert.match(html, /admin_sess_123/);
  assert.match(html, /Destructive actions/);
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
  assert.match(html, /Revoke user/);
  assert.match(html, /Restore user/);
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
  const html = renderApp(state);
  assert.match(html, /Sessions/);
  assert.match(html, /sess_1/);
  assert.match(html, /Revoke session/);
});

test('session action error mapping keeps session UX stable', () => {
  assert.equal(mapSessionActionError('forbidden'), 'Your current role is read-only and cannot revoke sessions.');
  assert.equal(mapSessionActionError('not_found'), 'The requested session could not be found.');
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
  assert.match(html, /Unbind device/);
  assert.match(html, /Disable device/);
  assert.match(html, /Rebind device/);
});

test('audit page renders audit log list layout', () => {
  const state = createInitialState('audit-logs');
  state.session = session;
  state.status = 'ready';
  state.auditPage.items = auditLogs;
  const html = renderApp(state);
  assert.match(html, /Audit logs/);
  assert.match(html, /authorization_user_revoked/);
  assert.match(html, /Refresh audit logs/);
});
