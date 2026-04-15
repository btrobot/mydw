export type RouteId = 'login' | 'dashboard' | 'users' | 'devices' | 'sessions' | 'audit-logs';

export interface AdminIdentity {
  id: string;
  username: string;
  display_name?: string | null;
  role: string;
}

export interface AdminSession {
  session_id: string;
  expires_at: string;
  user: AdminIdentity;
}

export interface AdminUserRecord {
  id: string;
  username: string;
  display_name?: string | null;
  email?: string | null;
  tenant_id?: string | null;
  status?: string | null;
  license_status?: string | null;
  license_expires_at?: string | null;
  entitlements: string[];
  device_count?: number | null;
  last_seen_at?: string | null;
}

export interface LoginFormState {
  username: string;
  password: string;
  submitting: boolean;
  errorMessage: string | null;
}

export interface UserEditorState {
  displayName: string;
  licenseStatus: string;
  licenseExpiresAt: string;
  entitlementsCsv: string;
  saving: boolean;
  feedback: string | null;
  errorMessage: string | null;
}

export interface UsersPageState {
  items: AdminUserRecord[];
  selectedUserId: string | null;
  detail: AdminUserRecord | null;
  loading: boolean;
  errorMessage: string | null;
  detailLoading: boolean;
  editor: UserEditorState;
}

export interface AdminDeviceRecord {
  device_id: string;
  user_id?: string | null;
  device_status: string;
  first_bound_at?: string | null;
  last_seen_at?: string | null;
  client_version?: string | null;
}

export interface DeviceEditorState {
  rebindUserId: string;
  rebindClientVersion: string;
  saving: boolean;
  feedback: string | null;
  errorMessage: string | null;
}

export interface DevicesPageState {
  items: AdminDeviceRecord[];
  selectedDeviceId: string | null;
  detail: AdminDeviceRecord | null;
  loading: boolean;
  errorMessage: string | null;
  detailLoading: boolean;
  editor: DeviceEditorState;
}

export interface AdminSessionRecord {
  session_id: string;
  user_id?: string | null;
  device_id?: string | null;
  auth_state: string;
  issued_at: string;
  expires_at: string;
  last_seen_at: string;
}

export interface SessionsPageState {
  items: AdminSessionRecord[];
  loading: boolean;
  errorMessage: string | null;
  selectedSessionId: string | null;
  feedback: string | null;
}

export interface AdminAuditRecord {
  id: string;
  event_type: string;
  actor_type?: string | null;
  actor_id?: string | null;
  target_user_id?: string | null;
  target_device_id?: string | null;
  target_session_id?: string | null;
  created_at: string;
  details: Record<string, unknown>;
}

export interface AuditPageState {
  items: AdminAuditRecord[];
  loading: boolean;
  errorMessage: string | null;
  filterEventType: string;
}

export interface DashboardMetricsState {
  activeSessions: number;
  loginFailures: number;
  deviceMismatches: number;
  destructiveActions: number;
  loading: boolean;
  errorMessage: string | null;
}

export interface AppState {
  route: RouteId;
  session: AdminSession | null;
  status: 'idle' | 'loading' | 'ready';
  globalError: string | null;
  loginForm: LoginFormState;
  usersPage: UsersPageState;
  devicesPage: DevicesPageState;
  sessionsPage: SessionsPageState;
  auditPage: AuditPageState;
  dashboardMetrics: DashboardMetricsState;
}

const ROUTE_LABELS: Record<RouteId, string> = {
  login: 'Login',
  dashboard: 'Dashboard',
  users: 'Users',
  devices: 'Devices',
  sessions: 'Sessions',
  'audit-logs': 'Audit Logs',
};

export function normalizeHash(hash: string): RouteId {
  const normalized = hash.replace(/^#/, '').replace(/^\/?/, '');
  switch (normalized) {
    case '':
    case 'dashboard':
      return 'dashboard';
    case 'login':
      return 'login';
    case 'users':
      return 'users';
    case 'devices':
      return 'devices';
    case 'sessions':
      return 'sessions';
    case 'audit-logs':
      return 'audit-logs';
    default:
      return 'dashboard';
  }
}

export function routeHref(route: RouteId): string {
  return route === 'login' ? '#/login' : `#/${route}`;
}

export function resolveGuardedRoute(route: RouteId, isAuthenticated: boolean): { route: RouteId; redirectTo: string | null } {
  if (!isAuthenticated && route !== 'login') {
    return { route: 'login', redirectTo: routeHref('login') };
  }
  if (isAuthenticated && route === 'login') {
    return { route: 'dashboard', redirectTo: routeHref('dashboard') };
  }
  return { route, redirectTo: null };
}

export function createInitialState(route: RouteId): AppState {
  return {
    route,
    session: null,
    status: 'idle',
    globalError: null,
    loginForm: {
      username: 'admin',
      password: '',
      submitting: false,
      errorMessage: null,
    },
    usersPage: {
      items: [],
      selectedUserId: null,
      detail: null,
      loading: false,
      errorMessage: null,
      detailLoading: false,
      editor: {
        displayName: '',
        licenseStatus: 'active',
        licenseExpiresAt: '',
        entitlementsCsv: '',
        saving: false,
        feedback: null,
        errorMessage: null,
      },
    },
    devicesPage: {
      items: [],
      selectedDeviceId: null,
      detail: null,
      loading: false,
      errorMessage: null,
      detailLoading: false,
      editor: {
        rebindUserId: '',
        rebindClientVersion: '0.2.0',
        saving: false,
        feedback: null,
        errorMessage: null,
      },
    },
    sessionsPage: {
      items: [],
      loading: false,
      errorMessage: null,
      selectedSessionId: null,
      feedback: null,
    },
    auditPage: {
      items: [],
      loading: false,
      errorMessage: null,
      filterEventType: '',
    },
    dashboardMetrics: {
      activeSessions: 0,
      loginFailures: 0,
      deviceMismatches: 0,
      destructiveActions: 0,
      loading: false,
      errorMessage: null,
    },
  };
}

export function mapLoginError(errorCode?: string): string {
  switch (errorCode) {
    case 'invalid_credentials':
      return 'Incorrect username or password.';
    case 'too_many_requests':
      return 'Too many attempts. Please retry later.';
    case 'forbidden':
      return 'This admin account is not allowed to sign in.';
    default:
      return 'Login failed. Please retry.';
  }
}

export function mapAdminActionError(errorCode?: string): string {
  switch (errorCode) {
    case 'forbidden':
      return 'Your current role is read-only and cannot perform this action.';
    case 'not_found':
      return 'The requested user could not be found.';
    default:
      return 'The action failed. Please retry.';
  }
}

export function mapDeviceActionError(errorCode?: string): string {
  switch (errorCode) {
    case 'forbidden':
      return 'Your current role is read-only and cannot perform this device action.';
    case 'not_found':
      return 'The requested device could not be found.';
    default:
      return 'The device action failed. Please retry.';
  }
}

export function mapSessionActionError(errorCode?: string): string {
  switch (errorCode) {
    case 'forbidden':
      return 'Your current role is read-only and cannot revoke sessions.';
    case 'not_found':
      return 'The requested session could not be found.';
    default:
      return 'The session action failed. Please retry.';
  }
}

export function createUserEditor(detail: AdminUserRecord | null): UserEditorState {
  return {
    displayName: detail?.display_name ?? '',
    licenseStatus: detail?.license_status ?? 'active',
    licenseExpiresAt: detail?.license_expires_at ? detail.license_expires_at.slice(0, 16) : '',
    entitlementsCsv: detail?.entitlements.join(', ') ?? '',
    saving: false,
    feedback: null,
    errorMessage: null,
  };
}

export function createDeviceEditor(detail: AdminDeviceRecord | null): DeviceEditorState {
  return {
    rebindUserId: detail?.user_id ?? '',
    rebindClientVersion: detail?.client_version ?? '0.2.0',
    saving: false,
    feedback: null,
    errorMessage: null,
  };
}

export function canEditUsers(session: AdminSession | null): boolean {
  return session?.user.role === 'super_admin' || session?.user.role === 'auth_admin';
}

export function renderApp(state: AppState): string {
  if (state.status === 'loading') {
    return wrapDocument(renderLoadingState());
  }
  if (!state.session) {
    return wrapDocument(renderLoginPage(state));
  }
  return wrapDocument(renderShell(state));
}

function wrapDocument(content: string): string {
  return `
    <div class="remote-admin-app">
      <style>
        :root { color-scheme: light; font-family: Inter, Arial, sans-serif; }
        body { margin: 0; background: #f5f7fb; color: #1f2937; }
        .remote-admin-app { min-height: 100vh; }
        .auth-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
        .card { background: #fff; border-radius: 16px; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08); padding: 24px; }
        .login-card { width: min(420px, 100%); }
        .eyebrow { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: #6366f1; font-weight: 700; }
        h1, h2, h3 { margin: 0 0 12px; }
        p { margin: 0 0 12px; line-height: 1.5; color: #4b5563; }
        form { display: grid; gap: 12px; margin-top: 16px; }
        label { display: grid; gap: 6px; font-size: 14px; color: #374151; font-weight: 600; }
        input, select, textarea { border: 1px solid #d1d5db; border-radius: 10px; padding: 12px 14px; font: inherit; width: 100%; box-sizing: border-box; }
        textarea { min-height: 96px; resize: vertical; }
        button { border: 0; border-radius: 10px; padding: 12px 16px; font: inherit; font-weight: 600; cursor: pointer; }
        button[disabled] { opacity: .6; cursor: not-allowed; }
        .primary { background: #4f46e5; color: #fff; }
        .secondary { background: #e5e7eb; color: #1f2937; }
        .danger { background: #dc2626; color: #fff; }
        .success { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; border-radius: 10px; padding: 12px 14px; }
        .error { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; border-radius: 10px; padding: 12px 14px; }
        .hint { font-size: 13px; color: #6b7280; }
        .shell { display: grid; grid-template-columns: 220px 1fr; min-height: 100vh; }
        .sidebar { background: #111827; color: #f9fafb; padding: 24px 18px; display: grid; gap: 20px; }
        .brand { display: grid; gap: 6px; }
        .brand strong { font-size: 18px; }
        .brand span { color: #9ca3af; font-size: 13px; }
        .nav { display: grid; gap: 8px; }
        .nav a { color: #d1d5db; text-decoration: none; padding: 10px 12px; border-radius: 10px; }
        .nav a.active { background: #374151; color: #fff; }
        .main { padding: 24px; display: grid; gap: 24px; }
        .topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
        .pill { background: #eef2ff; color: #4338ca; border-radius: 999px; padding: 6px 10px; font-size: 12px; font-weight: 700; }
        .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
        .metric { background: #fff; border-radius: 14px; padding: 18px; border: 1px solid #e5e7eb; }
        .metric strong { display: block; font-size: 28px; margin-bottom: 8px; }
        .placeholder { display: grid; gap: 12px; }
        .placeholder ul { margin: 0; padding-left: 18px; color: #4b5563; }
        .users-layout { display: grid; grid-template-columns: minmax(280px, 360px) 1fr; gap: 20px; align-items: start; }
        .users-list { display: grid; gap: 10px; }
        .user-card { border: 1px solid #e5e7eb; border-radius: 14px; background: #fff; padding: 14px; display: grid; gap: 6px; cursor: pointer; }
        .user-card.active { border-color: #4f46e5; box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15); }
        .user-meta { display: flex; gap: 8px; flex-wrap: wrap; font-size: 12px; color: #6b7280; }
        .tag { background: #f3f4f6; color: #374151; border-radius: 999px; padding: 4px 8px; font-size: 12px; font-weight: 600; }
        .toolbar { display: flex; gap: 10px; flex-wrap: wrap; }
        .detail-grid { display: grid; gap: 16px; }
      </style>
      ${content}
    </div>
  `;
}

function renderLoadingState(): string {
  return `
    <div class="auth-page">
      <section class="card login-card">
        <div class="eyebrow">Remote Admin</div>
        <h1>Restoring admin session…</h1>
        <p>Please wait while the control plane restores your sign-in state.</p>
      </section>
    </div>
  `;
}

function renderLoginPage(state: AppState): string {
  const statusLabel = state.loginForm.submitting ? 'Signing in…' : 'Sign in';
  return `
    <div class="auth-page">
      <section class="card login-card">
        <div class="eyebrow">Remote Admin</div>
        <h1>Remote authorization console</h1>
        <p>Sign in with an independent admin account to enter the protected control plane.</p>
        ${state.globalError ? `<div class="error" data-testid="global-error">${escapeHtml(state.globalError)}</div>` : ''}
        ${state.loginForm.errorMessage ? `<div class="error" data-testid="login-error">${escapeHtml(state.loginForm.errorMessage)}</div>` : ''}
        <form id="admin-login-form">
          <label>
            Username
            <input id="admin-username" name="username" autocomplete="username" value="${escapeHtml(state.loginForm.username)}" />
          </label>
          <label>
            Password
            <input id="admin-password" name="password" type="password" autocomplete="current-password" value="${escapeHtml(state.loginForm.password)}" />
          </label>
          <button class="primary" type="submit" ${state.loginForm.submitting ? 'disabled' : ''}>${statusLabel}</button>
        </form>
        <p class="hint">Development seeds include <code>admin</code>, <code>auth-admin</code>, and <code>support</code>.</p>
      </section>
    </div>
  `;
}

function renderShell(state: AppState): string {
  const route = state.route === 'login' ? 'dashboard' : state.route;
  return `
    <div class="shell">
      <aside class="sidebar">
        <div class="brand">
          <strong>Remote Admin</strong>
          <span>Phase 2 thin admin operations</span>
        </div>
        <nav class="nav">
          ${(['dashboard', 'users', 'devices', 'sessions', 'audit-logs'] as const)
            .map(
              (navRoute) =>
                `<a href="${routeHref(navRoute)}" class="${route === navRoute ? 'active' : ''}">${ROUTE_LABELS[navRoute]}</a>`,
            )
            .join('')}
        </nav>
      </aside>
      <main class="main">
        <header class="topbar">
          <div>
            <div class="eyebrow">Authenticated admin</div>
            <h1>${ROUTE_LABELS[route]}</h1>
          </div>
          <div style="display:flex; align-items:center; gap: 12px;">
            <span class="pill">${escapeHtml(state.session?.user.role ?? 'admin')}</span>
            <button id="admin-logout" class="secondary" type="button">Sign out</button>
          </div>
        </header>
        ${renderRouteBody(route, state)}
      </main>
    </div>
  `;
}

function renderRouteBody(route: Exclude<RouteId, 'login'>, state: AppState): string {
  if (route === 'dashboard') {
    const metrics = state.dashboardMetrics;
    return `
      <section class="grid">
        ${[
          { label: 'Active sessions', value: String(metrics.activeSessions), hint: 'Live active end-user sessions.' },
          { label: 'Login failures', value: String(metrics.loginFailures), hint: 'Aggregated auth + admin login failures.' },
          { label: 'Device mismatches', value: String(metrics.deviceMismatches), hint: 'Detected mismatch denials from the audit stream.' },
          { label: 'Destructive actions', value: String(metrics.destructiveActions), hint: 'Admin revoke/unbind/disable/rebind/session revoke actions.' },
        ]
          .map(
            (metric) => `
              <article class="metric">
                <span class="eyebrow">${metric.label}</span>
                <strong>${metric.value}</strong>
                <p>${metric.hint}</p>
              </article>
            `,
          )
          .join('')}
      </section>
      ${metrics.errorMessage ? `<div class="error">${escapeHtml(metrics.errorMessage)}</div>` : ''}
      <section class="card placeholder">
        <h2>Dashboard operations snapshot</h2>
        <p>Phase 2.5 turns the dashboard into a lightweight supportability surface backed by real metrics.</p>
        <ul>
          <li>Current admin: ${escapeHtml(state.session?.user.display_name ?? state.session?.user.username ?? 'admin')}</li>
          <li>Session ID: <code>${escapeHtml(state.session?.session_id ?? '')}</code></li>
          <li>Expires at: ${escapeHtml(state.session?.expires_at ?? '')}</li>
        </ul>
      </section>
    `;
  }
  if (route === 'users') {
    return renderUsersRoute(state);
  }
  if (route === 'devices') {
    return renderDevicesRoute(state);
  }
  if (route === 'sessions') {
    return renderSessionsRoute(state);
  }
  if (route === 'audit-logs') {
    return renderAuditLogsRoute(state);
  }
  return `
    <section class="card placeholder">
      <div class="eyebrow">Protected placeholder</div>
      <h2>Unsupported route</h2>
      <p>This route is not currently implemented.</p>
    </section>
  `;
}

function renderUsersRoute(state: AppState): string {
  const canWrite = canEditUsers(state.session);
  const usersPage = state.usersPage;
  return `
    <section class="users-layout">
      <article class="card">
        <div class="eyebrow">Admin users API</div>
        <h2>Users</h2>
        <p>Review current authorization state, then open detail to update or execute revoke / restore.</p>
        ${usersPage.errorMessage ? `<div class="error">${escapeHtml(usersPage.errorMessage)}</div>` : ''}
        <div class="users-list" data-testid="users-list">
          ${usersPage.loading ? '<p>Loading users…</p>' : ''}
          ${!usersPage.loading && usersPage.items.length === 0 ? '<p>No managed users were returned.</p>' : ''}
          ${usersPage.items
            .map((user) => {
              const active = user.id === usersPage.selectedUserId ? 'active' : '';
              return `
                <button class="user-card ${active}" type="button" data-user-id="${user.id}">
                  <strong>${escapeHtml(user.display_name ?? user.username)}</strong>
                  <span>${escapeHtml(user.username)}</span>
                  <div class="user-meta">
                    <span class="tag">status:${escapeHtml(user.status ?? 'unknown')}</span>
                    <span class="tag">license:${escapeHtml(user.license_status ?? 'unknown')}</span>
                    <span class="tag">devices:${String(user.device_count ?? 0)}</span>
                  </div>
                </button>
              `;
            })
            .join('')}
        </div>
      </article>
      <article class="card detail-grid">
        <div class="eyebrow">Authorization detail</div>
        <h2>${usersPage.detail ? escapeHtml(usersPage.detail.username) : 'Select a user'}</h2>
        ${usersPage.detailLoading ? '<p>Loading detail…</p>' : ''}
        ${!usersPage.detail && !usersPage.detailLoading ? '<p>Select a user from the list to inspect and control authorization.</p>' : ''}
        ${usersPage.detail ? renderUserDetail(usersPage.detail, usersPage.editor, canWrite) : ''}
      </article>
    </section>
  `;
}

function renderDevicesRoute(state: AppState): string {
  const canWrite = canEditUsers(state.session);
  const devicesPage = state.devicesPage;
  return `
    <section class="users-layout">
      <article class="card">
        <div class="eyebrow">Admin devices API</div>
        <h2>Devices</h2>
        <p>Inspect the current binding, then unbind, disable, or rebind the device to a managed user.</p>
        ${devicesPage.errorMessage ? `<div class="error">${escapeHtml(devicesPage.errorMessage)}</div>` : ''}
        <div class="users-list" data-testid="devices-list">
          ${devicesPage.loading ? '<p>Loading devices…</p>' : ''}
          ${!devicesPage.loading && devicesPage.items.length === 0 ? '<p>No devices were returned.</p>' : ''}
          ${devicesPage.items
            .map((device) => {
              const active = device.device_id === devicesPage.selectedDeviceId ? 'active' : '';
              return `
                <button class="user-card ${active}" type="button" data-device-id="${device.device_id}">
                  <strong>${escapeHtml(device.device_id)}</strong>
                  <span>${escapeHtml(device.user_id ?? 'unbound')}</span>
                  <div class="user-meta">
                    <span class="tag">status:${escapeHtml(device.device_status)}</span>
                    <span class="tag">client:${escapeHtml(device.client_version ?? 'n/a')}</span>
                  </div>
                </button>
              `;
            })
            .join('')}
        </div>
      </article>
      <article class="card detail-grid">
        <div class="eyebrow">Device control</div>
        <h2>${devicesPage.detail ? escapeHtml(devicesPage.detail.device_id) : 'Select a device'}</h2>
        ${devicesPage.detailLoading ? '<p>Loading detail…</p>' : ''}
        ${!devicesPage.detail && !devicesPage.detailLoading ? '<p>Select a device from the list to inspect and control binding state.</p>' : ''}
        ${devicesPage.detail ? renderDeviceDetail(devicesPage.detail, devicesPage.editor, canWrite) : ''}
      </article>
    </section>
  `;
}

function renderUserDetail(detail: AdminUserRecord, editor: UserEditorState, canWrite: boolean): string {
  return `
    <div class="detail-grid" data-testid="user-detail">
      ${editor.feedback ? `<div class="success">${escapeHtml(editor.feedback)}</div>` : ''}
      ${editor.errorMessage ? `<div class="error">${escapeHtml(editor.errorMessage)}</div>` : ''}
      <div class="user-meta">
        <span class="tag">tenant:${escapeHtml(detail.tenant_id ?? 'n/a')}</span>
        <span class="tag">last seen:${escapeHtml(detail.last_seen_at ?? 'n/a')}</span>
      </div>
      <form id="admin-user-form">
        <label>
          Display name
          <input id="user-display-name" value="${escapeHtml(editor.displayName)}" ${canWrite ? '' : 'disabled'} />
        </label>
        <label>
          License status
          <select id="user-license-status" ${canWrite ? '' : 'disabled'}>
            ${['active', 'disabled', 'revoked'].map((status) => `<option value="${status}" ${editor.licenseStatus === status ? 'selected' : ''}>${status}</option>`).join('')}
          </select>
        </label>
        <label>
          License expires at
          <input id="user-license-expires-at" type="datetime-local" value="${escapeHtml(editor.licenseExpiresAt)}" ${canWrite ? '' : 'disabled'} />
        </label>
        <label>
          Entitlements (comma separated)
          <textarea id="user-entitlements" ${canWrite ? '' : 'disabled'}>${escapeHtml(editor.entitlementsCsv)}</textarea>
        </label>
        <div class="toolbar">
          <button id="user-save" class="primary" type="submit" ${canWrite && !editor.saving ? '' : 'disabled'}>${editor.saving ? 'Saving…' : 'Save changes'}</button>
          <button id="user-revoke" class="danger" type="button" ${canWrite ? '' : 'disabled'}>Revoke user</button>
          <button id="user-restore" class="secondary" type="button" ${canWrite ? '' : 'disabled'}>Restore user</button>
        </div>
      </form>
      ${!canWrite ? '<p class="hint">This admin role is read-only. Destructive and update actions are disabled.</p>' : ''}
    </div>
  `;
}

function renderDeviceDetail(detail: AdminDeviceRecord, editor: DeviceEditorState, canWrite: boolean): string {
  return `
    <div class="detail-grid" data-testid="device-detail">
      ${editor.feedback ? `<div class="success">${escapeHtml(editor.feedback)}</div>` : ''}
      ${editor.errorMessage ? `<div class="error">${escapeHtml(editor.errorMessage)}</div>` : ''}
      <div class="user-meta">
        <span class="tag">bound user:${escapeHtml(detail.user_id ?? 'unbound')}</span>
        <span class="tag">last seen:${escapeHtml(detail.last_seen_at ?? 'n/a')}</span>
      </div>
      <form id="admin-device-form">
        <label>
          Target user id
          <input id="device-rebind-user-id" value="${escapeHtml(editor.rebindUserId)}" ${canWrite ? '' : 'disabled'} />
        </label>
        <label>
          Client version
          <input id="device-rebind-client-version" value="${escapeHtml(editor.rebindClientVersion)}" ${canWrite ? '' : 'disabled'} />
        </label>
        <div class="toolbar">
          <button id="device-unbind" class="secondary" type="button" ${canWrite ? '' : 'disabled'}>Unbind device</button>
          <button id="device-disable" class="danger" type="button" ${canWrite ? '' : 'disabled'}>Disable device</button>
          <button id="device-rebind" class="primary" type="submit" ${canWrite && !editor.saving ? '' : 'disabled'}>${editor.saving ? 'Rebinding…' : 'Rebind device'}</button>
        </div>
      </form>
      ${!canWrite ? '<p class="hint">This admin role is read-only. Device actions are disabled.</p>' : ''}
    </div>
  `;
}

function renderSessionsRoute(state: AppState): string {
  const canWrite = canEditUsers(state.session);
  const sessionsPage = state.sessionsPage;
  return `
    <section class="card detail-grid">
      <div class="eyebrow">Admin sessions API</div>
      <h2>Sessions</h2>
      <p>Review active authorization sessions and revoke them when a controlled cut-off is required.</p>
      ${sessionsPage.feedback ? `<div class="success">${escapeHtml(sessionsPage.feedback)}</div>` : ''}
      ${sessionsPage.errorMessage ? `<div class="error">${escapeHtml(sessionsPage.errorMessage)}</div>` : ''}
      ${sessionsPage.loading ? '<p>Loading sessions…</p>' : ''}
      ${!sessionsPage.loading && sessionsPage.items.length === 0 ? '<p>No sessions were returned.</p>' : ''}
      <div class="users-list" data-testid="sessions-list">
        ${sessionsPage.items
          .map((session) => {
            const active = session.session_id === sessionsPage.selectedSessionId ? 'active' : '';
            return `
              <div class="user-card ${active}">
                <strong>${escapeHtml(session.session_id)}</strong>
                <span>${escapeHtml(session.user_id ?? 'unknown user')}</span>
                <div class="user-meta">
                  <span class="tag">device:${escapeHtml(session.device_id ?? 'unknown')}</span>
                  <span class="tag">state:${escapeHtml(session.auth_state)}</span>
                  <span class="tag">last seen:${escapeHtml(session.last_seen_at)}</span>
                </div>
                <div class="toolbar">
                  <button class="danger" data-session-id="${session.session_id}" ${canWrite ? '' : 'disabled'}>Revoke session</button>
                </div>
              </div>
            `;
          })
          .join('')}
      </div>
      ${!canWrite ? '<p class="hint">This admin role is read-only. Session revoke actions are disabled.</p>' : ''}
    </section>
  `;
}

function renderAuditLogsRoute(state: AppState): string {
  const auditPage = state.auditPage;
  return `
    <section class="card detail-grid">
      <div class="eyebrow">Admin audit API</div>
      <h2>Audit logs</h2>
      <p>Inspect destructive actions and auth failures with a lightweight event filter.</p>
      ${auditPage.errorMessage ? `<div class="error">${escapeHtml(auditPage.errorMessage)}</div>` : ''}
      <form id="admin-audit-form">
        <label>
          Event type
          <input id="audit-event-type" value="${escapeHtml(auditPage.filterEventType)}" placeholder="e.g. authorization_user_revoked" />
        </label>
        <div class="toolbar">
          <button id="audit-refresh" class="primary" type="submit">Refresh audit logs</button>
        </div>
      </form>
      ${auditPage.loading ? '<p>Loading audit logs…</p>' : ''}
      ${!auditPage.loading && auditPage.items.length === 0 ? '<p>No audit events were returned.</p>' : ''}
      <div class="users-list" data-testid="audit-list">
        ${auditPage.items
          .map(
            (row) => `
              <div class="user-card">
                <strong>${escapeHtml(row.event_type)}</strong>
                <span>${escapeHtml(row.created_at)}</span>
                <div class="user-meta">
                  <span class="tag">actor:${escapeHtml(row.actor_id ?? 'n/a')}</span>
                  <span class="tag">user:${escapeHtml(row.target_user_id ?? 'n/a')}</span>
                  <span class="tag">device:${escapeHtml(row.target_device_id ?? 'n/a')}</span>
                  <span class="tag">session:${escapeHtml(row.target_session_id ?? 'n/a')}</span>
                </div>
              </div>
            `,
          )
          .join('')}
      </div>
    </section>
  `;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
