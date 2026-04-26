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
  detailErrorMessage: string | null;
  filters: {
    query: string;
    status: string;
    licenseStatus: string;
  };
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
  detailErrorMessage: string | null;
  filters: {
    query: string;
    status: string;
    userId: string;
  };
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
  actionInFlightId: string | null;
  filters: {
    query: string;
    authState: string;
    userId: string;
    deviceId: string;
  };
}

export interface AdminAuditRecord {
  id: string;
  event_type: string;
  actor_type?: string | null;
  actor_id?: string | null;
  target_user_id?: string | null;
  target_device_id?: string | null;
  target_session_id?: string | null;
  request_id?: string | null;
  trace_id?: string | null;
  created_at: string;
  details: Record<string, unknown>;
}

export interface AuditFiltersState {
  eventType: string;
  actorId: string;
  targetUserId: string;
  targetDeviceId: string;
  targetSessionId: string;
  createdFrom: string;
  createdTo: string;
  limit: number;
  offset: number;
}

export interface AuditPageState {
  items: AdminAuditRecord[];
  total: number;
  selectedAuditId: string | null;
  loading: boolean;
  errorMessage: string | null;
  filters: AuditFiltersState;
}

export interface DashboardMetricsState {
  activeSessions: number;
  loginFailures: number;
  deviceMismatches: number;
  destructiveActions: number;
  generatedAt: string | null;
  recentFailures: AdminAuditRecord[];
  recentDestructiveActions: AdminAuditRecord[];
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
      detailErrorMessage: null,
      filters: {
        query: '',
        status: '',
        licenseStatus: '',
      },
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
      detailErrorMessage: null,
      filters: {
        query: '',
        status: '',
        userId: '',
      },
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
      actionInFlightId: null,
      filters: {
        query: '',
        authState: '',
        userId: '',
        deviceId: '',
      },
    },
    auditPage: {
      items: [],
      total: 0,
      selectedAuditId: null,
      loading: false,
      errorMessage: null,
      filters: {
        eventType: '',
        actorId: '',
        targetUserId: '',
        targetDeviceId: '',
        targetSessionId: '',
        createdFrom: '',
        createdTo: '',
        limit: 25,
        offset: 0,
      },
    },
    dashboardMetrics: {
      activeSessions: 0,
      loginFailures: 0,
      deviceMismatches: 0,
      destructiveActions: 0,
      generatedAt: null,
      recentFailures: [],
      recentDestructiveActions: [],
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

export function buildAuditLogQuery(filters: AuditFiltersState): string {
  const params = new URLSearchParams();
  if (filters.eventType) params.set('event_type', filters.eventType);
  if (filters.actorId) params.set('actor_id', filters.actorId);
  if (filters.targetUserId) params.set('target_user_id', filters.targetUserId);
  if (filters.targetDeviceId) params.set('target_device_id', filters.targetDeviceId);
  if (filters.targetSessionId) params.set('target_session_id', filters.targetSessionId);
  if (filters.createdFrom) params.set('created_from', toUtcAuditFilterTimestamp(filters.createdFrom, 'start'));
  if (filters.createdTo) params.set('created_to', toUtcAuditFilterTimestamp(filters.createdTo, 'end'));
  params.set('limit', String(filters.limit));
  params.set('offset', String(filters.offset));
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function buildUsersQuery(filters: UsersPageState['filters']): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.status) params.set('status', filters.status);
  if (filters.licenseStatus) params.set('license_status', filters.licenseStatus);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function buildDevicesQuery(filters: DevicesPageState['filters']): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.status) params.set('device_status', filters.status);
  if (filters.userId) params.set('user_id', filters.userId);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function buildSessionsQuery(filters: SessionsPageState['filters']): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.authState) params.set('auth_state', filters.authState);
  if (filters.userId) params.set('user_id', filters.userId);
  if (filters.deviceId) params.set('device_id', filters.deviceId);
  const query = params.toString();
  return query ? `?${query}` : '';
}

function toUtcAuditFilterTimestamp(localValue: string, boundary: 'start' | 'end'): string {
  const date = new Date(localValue);
  if (Number.isNaN(date.getTime())) {
    return localValue;
  }
  if (boundary === 'end') {
    date.setSeconds(59, 999);
  } else {
    date.setSeconds(0, 0);
  }
  return date.toISOString();
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
        .sidebar { background: #111827; color: #f9fafb; padding: 24px 18px; display: flex; flex-direction: column; gap: 16px; }
        .brand { display: grid; gap: 6px; }
        .brand strong { font-size: 18px; }
        .brand span { color: #9ca3af; font-size: 13px; }
        .nav { display: flex; flex-direction: column; gap: 8px; }
        .nav a { color: #d1d5db; text-decoration: none; padding: 10px 12px; border-radius: 10px; }
        .nav a.active { background: #374151; color: #fff; }
        .main { padding: 24px; display: grid; gap: 24px; }
        .topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
        .pill { background: #eef2ff; color: #4338ca; border-radius: 999px; padding: 6px 10px; font-size: 12px; font-weight: 700; }
        .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
        .metric { background: #fff; border-radius: 14px; padding: 18px; border: 1px solid #e5e7eb; }
        .metric strong { display: block; font-size: 28px; margin-bottom: 8px; }
        .metric a { color: inherit; text-decoration: none; display: block; }
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
        .filters-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
        .list-toolbar { display: grid; gap: 12px; margin-bottom: 12px; }
        .stack { display: grid; gap: 16px; }
        .summary-list, .detail-list { display: grid; gap: 10px; }
        .summary-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
        .summary-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; display: grid; gap: 6px; }
        .summary-item strong { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: #64748b; }
        .detail-list pre { margin: 0; background: #111827; color: #f9fafb; padding: 12px; border-radius: 12px; overflow: auto; }
        .empty-state { border: 1px dashed #cbd5e1; border-radius: 14px; padding: 16px; color: #64748b; background: #f8fafc; }
        .inline-meta { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: center; }
        .inline-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .muted-link { color: #4f46e5; font-weight: 600; text-decoration: none; }
        .tag-success { background: #dcfce7; color: #166534; }
        .tag-warning { background: #fef3c7; color: #92400e; }
        .tag-danger { background: #fee2e2; color: #b91c1c; }
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
          <span>Phase 3 operational console</span>
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
    return renderDashboardRoute(state);
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
        <p>Search by username, display name, email, or user id, then inspect the selected user in the detail panel.</p>
        <form id="users-filter-form" class="list-toolbar">
          <div class="filters-grid">
            <label>
              Search
              <input id="users-query" value="${escapeHtml(usersPage.filters.query)}" placeholder="alice / alice@example.com / u_1" />
            </label>
            <label>
              Status
              <select id="users-status-filter">
                ${renderSelectOptions(
                  [
                    { value: '', label: 'All statuses' },
                    { value: 'active', label: 'active' },
                    { value: 'disabled', label: 'disabled' },
                  ],
                  usersPage.filters.status,
                )}
              </select>
            </label>
            <label>
              License
              <select id="users-license-filter">
                ${renderSelectOptions(
                  [
                    { value: '', label: 'All licenses' },
                    { value: 'active', label: 'active' },
                    { value: 'disabled', label: 'disabled' },
                    { value: 'revoked', label: 'revoked' },
                  ],
                  usersPage.filters.licenseStatus,
                )}
              </select>
            </label>
          </div>
          <div class="toolbar">
            <button id="users-filter-submit" class="primary" type="submit">Apply filters</button>
            <button id="users-filter-clear" class="secondary" type="button">Clear filters</button>
          </div>
        </form>
        <p class="hint">Showing ${String(usersPage.items.length)} users from the current filtered result set.</p>
        ${usersPage.errorMessage ? renderRetryableError(usersPage.errorMessage, 'users-retry') : ''}
        <div class="users-list" data-testid="users-list">
          ${usersPage.loading ? '<p>Loading users...</p>' : ''}
          ${!usersPage.loading && !usersPage.errorMessage && usersPage.items.length === 0 ? '<div class="empty-state">No managed users matched the current filters.</div>' : ''}
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
        ${usersPage.detailLoading ? '<p>Loading detail...</p>' : ''}
        ${usersPage.detailErrorMessage ? renderRetryableError(usersPage.detailErrorMessage, 'user-detail-retry') : ''}
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
        <p>Search by device id, user id, or version, then inspect the selected device before changing its binding state.</p>
        <form id="devices-filter-form" class="list-toolbar">
          <div class="filters-grid">
            <label>
              Search
              <input id="devices-query" value="${escapeHtml(devicesPage.filters.query)}" placeholder="device_1 / u_1 / 0.2.0" />
            </label>
            <label>
              Device status
              <select id="devices-status-filter">
                ${renderSelectOptions(
                  [
                    { value: '', label: 'All device states' },
                    { value: 'bound', label: 'bound' },
                    { value: 'unbound', label: 'unbound' },
                    { value: 'disabled', label: 'disabled' },
                  ],
                  devicesPage.filters.status,
                )}
              </select>
            </label>
            <label>
              Bound user
              <input id="devices-user-filter" value="${escapeHtml(devicesPage.filters.userId)}" placeholder="u_1" />
            </label>
          </div>
          <div class="toolbar">
            <button id="devices-filter-submit" class="primary" type="submit">Apply filters</button>
            <button id="devices-filter-clear" class="secondary" type="button">Clear filters</button>
          </div>
        </form>
        <p class="hint">Showing ${String(devicesPage.items.length)} devices from the current filtered result set.</p>
        ${devicesPage.errorMessage ? renderRetryableError(devicesPage.errorMessage, 'devices-retry') : ''}
        <div class="users-list" data-testid="devices-list">
          ${devicesPage.loading ? '<p>Loading devices...</p>' : ''}
          ${!devicesPage.loading && !devicesPage.errorMessage && devicesPage.items.length === 0 ? '<div class="empty-state">No devices matched the current filters.</div>' : ''}
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
        ${devicesPage.detailLoading ? '<p>Loading detail...</p>' : ''}
        ${devicesPage.detailErrorMessage ? renderRetryableError(devicesPage.detailErrorMessage, 'device-detail-retry') : ''}
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
      ${renderSummaryGrid([
        { label: 'User ID', value: detail.id },
        { label: 'Email', value: detail.email ?? 'n/a' },
        { label: 'Tenant', value: detail.tenant_id ?? 'n/a' },
        { label: 'Status', value: detail.status ?? 'n/a' },
        { label: 'License', value: detail.license_status ?? 'n/a' },
        { label: 'License expiry', value: detail.license_expires_at ?? 'n/a' },
        { label: 'Device count', value: String(detail.device_count ?? 0) },
        { label: 'Last seen', value: detail.last_seen_at ?? 'n/a' },
      ])}
      <div class="detail-list">
        <p><strong>Entitlements:</strong></p>
        <div class="user-meta">
          ${detail.entitlements.length > 0 ? detail.entitlements.map((entitlement) => `<span class="tag">${escapeHtml(entitlement)}</span>`).join('') : '<span class="tag">none</span>'}
        </div>
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
          <button id="user-save" class="primary" type="submit" ${canWrite && !editor.saving ? '' : 'disabled'}>${editor.saving ? 'Saving...' : 'Save changes'}</button>
          <button id="user-revoke" class="danger" type="button" ${canWrite ? '' : 'disabled'}>Revoke user</button>
          <button id="user-restore" class="secondary" type="button" ${canWrite ? '' : 'disabled'}>Restore user</button>
        </div>
      </form>
      <div class="empty-state">Danger-zone actions are audited and affect downstream sign-in, refresh, and device authorization immediately.</div>
      ${!canWrite ? '<p class="hint">This admin role is read-only. Destructive and update actions are disabled.</p>' : ''}
    </div>
  `;
}

function renderDeviceDetail(detail: AdminDeviceRecord, editor: DeviceEditorState, canWrite: boolean): string {
  return `
    <div class="detail-grid" data-testid="device-detail">
      ${editor.feedback ? `<div class="success">${escapeHtml(editor.feedback)}</div>` : ''}
      ${editor.errorMessage ? `<div class="error">${escapeHtml(editor.errorMessage)}</div>` : ''}
      ${renderSummaryGrid([
        { label: 'Device ID', value: detail.device_id },
        { label: 'Bound user', value: detail.user_id ?? 'unbound' },
        { label: 'Device status', value: detail.device_status },
        { label: 'Client version', value: detail.client_version ?? 'n/a' },
        { label: 'First bound', value: detail.first_bound_at ?? 'n/a' },
        { label: 'Last seen', value: detail.last_seen_at ?? 'n/a' },
      ])}
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
          <button id="device-rebind" class="primary" type="submit" ${canWrite && !editor.saving ? '' : 'disabled'}>${editor.saving ? 'Rebinding...' : 'Rebind device'}</button>
        </div>
      </form>
      <div class="empty-state">Binding changes are audited and can immediately force device mismatch or revoke existing session continuity.</div>
      ${!canWrite ? '<p class="hint">This admin role is read-only. Device actions are disabled.</p>' : ''}
    </div>
  `;
}

function renderSessionsRoute(state: AppState): string {
  const canWrite = canEditUsers(state.session);
  const sessionsPage = state.sessionsPage;
  const selectedSession = selectSessionRecord(sessionsPage);
  const revokeLabel =
    sessionsPage.actionInFlightId && selectedSession?.session_id === sessionsPage.actionInFlightId
      ? 'Revoking session...'
      : 'Revoke session';
  return `
    <section class="users-layout">
      <article class="card detail-grid">
        <div class="eyebrow">Admin sessions API</div>
        <h2>Sessions</h2>
        <p>Search by session, user, or device and inspect one session at a time before forcing revocation.</p>
        ${sessionsPage.feedback ? `<div class="success">${escapeHtml(sessionsPage.feedback)}</div>` : ''}
        <form id="sessions-filter-form" class="list-toolbar">
          <div class="filters-grid">
            <label>
              Search
              <input id="sessions-query" value="${escapeHtml(sessionsPage.filters.query)}" placeholder="sess_1 / u_1 / device_1" />
            </label>
            <label>
              Auth state
              <select id="sessions-auth-state-filter">
                ${renderSelectOptions(
                  [
                    { value: '', label: 'All states' },
                    { value: 'authenticated_active', label: 'authenticated_active' },
                    { value: 'authorization_disabled', label: 'authorization_disabled' },
                    { value: 'device_unbound', label: 'device_unbound' },
                    { value: 'device_disabled', label: 'device_disabled' },
                  ],
                  sessionsPage.filters.authState,
                )}
              </select>
            </label>
            <label>
              User
              <input id="sessions-user-filter" value="${escapeHtml(sessionsPage.filters.userId)}" placeholder="u_1" />
            </label>
            <label>
              Device
              <input id="sessions-device-filter" value="${escapeHtml(sessionsPage.filters.deviceId)}" placeholder="device_1" />
            </label>
          </div>
          <div class="toolbar">
            <button id="sessions-filter-submit" class="primary" type="submit">Apply filters</button>
            <button id="sessions-filter-clear" class="secondary" type="button">Clear filters</button>
          </div>
        </form>
        ${sessionsPage.errorMessage ? renderRetryableError(sessionsPage.errorMessage, 'sessions-retry') : ''}
        ${sessionsPage.loading ? '<p>Loading sessions...</p>' : ''}
        ${!sessionsPage.loading && !sessionsPage.errorMessage && sessionsPage.items.length === 0 ? '<div class="empty-state">No sessions matched the current filters.</div>' : ''}
        <div class="users-list" data-testid="sessions-list">
          ${sessionsPage.items
            .map((session) => {
              const active = session.session_id === sessionsPage.selectedSessionId ? 'active' : '';
              return `
                <button class="user-card ${active}" type="button" data-session-select-id="${session.session_id}">
                  <strong>${escapeHtml(session.session_id)}</strong>
                  <span>${escapeHtml(session.user_id ?? 'unknown user')}</span>
                  <div class="user-meta">
                    <span class="tag">device:${escapeHtml(session.device_id ?? 'unknown')}</span>
                    ${renderSessionStateBadge(session.auth_state)}
                  </div>
                  <div class="user-meta">
                    <span class="tag">issued:${escapeHtml(session.issued_at)}</span>
                    <span class="tag">expires:${escapeHtml(session.expires_at)}</span>
                    <span class="tag">last seen:${escapeHtml(session.last_seen_at)}</span>
                  </div>
                </button>
              `;
            })
            .join('')}
        </div>
        ${!canWrite ? '<p class="hint">This admin role is read-only. Session revoke actions are disabled.</p>' : ''}
      </article>
      <article class="card detail-grid">
        <div class="eyebrow">Session detail</div>
        <h2>${selectedSession ? escapeHtml(selectedSession.session_id) : 'Select a session'}</h2>
        ${selectedSession ? renderSessionDetail(selectedSession, canWrite, revokeLabel, sessionsPage.actionInFlightId === selectedSession.session_id) : '<div class="empty-state">Choose a session from the list to inspect auth state, timestamps, and revoke controls.</div>'}
      </article>
    </section>
  `;
}

function renderSummaryGrid(items: Array<{ label: string; value: string }>): string {
  return `
    <div class="summary-grid">
      ${items
        .map(
          (item) => `
            <div class="summary-item">
              <strong>${escapeHtml(item.label)}</strong>
              <span>${escapeHtml(item.value)}</span>
            </div>
          `,
        )
        .join('')}
    </div>
  `;
}

function renderSelectOptions(options: Array<{ value: string; label: string }>, selected: string): string {
  return options
    .map((option) => `<option value="${option.value}" ${option.value === selected ? 'selected' : ''}>${option.label}</option>`)
    .join('');
}

function selectSessionRecord(sessionsPage: SessionsPageState): AdminSessionRecord | null {
  return sessionsPage.items.find((session) => session.session_id === sessionsPage.selectedSessionId) ?? sessionsPage.items[0] ?? null;
}

function renderSessionDetail(detail: AdminSessionRecord, canWrite: boolean, revokeLabel: string, isRevoking: boolean): string {
  return `
    <div class="detail-grid" data-testid="session-detail">
      ${renderSummaryGrid([
        { label: 'Session ID', value: detail.session_id },
        { label: 'User', value: detail.user_id ?? 'n/a' },
        { label: 'Device', value: detail.device_id ?? 'n/a' },
        { label: 'Auth state', value: detail.auth_state },
        { label: 'Issued at', value: detail.issued_at },
        { label: 'Expires at', value: detail.expires_at },
        { label: 'Last seen', value: detail.last_seen_at },
      ])}
      <div class="user-meta">
        ${renderSessionStateBadge(detail.auth_state)}
      </div>
      <div class="toolbar">
        <button id="session-revoke" class="danger" type="button" data-session-id="${detail.session_id}" ${canWrite && !isRevoking ? '' : 'disabled'}>${revokeLabel}</button>
      </div>
      <div class="empty-state">Session revoke is audited and immediately invalidates subsequent me/refresh continuity for the affected session.</div>
    </div>
  `;
}

function renderSessionStateBadge(authState: string): string {
  return `<span class="tag ${sessionStateTone(authState)}">state:${escapeHtml(authState)}</span>`;
}

function sessionStateTone(authState: string): string {
  if (authState === 'authenticated_active') return 'tag-success';
  if (authState.startsWith('revoked:')) return 'tag-danger';
  return 'tag-warning';
}

function renderDashboardRoute(state: AppState): string {
  const metrics = state.dashboardMetrics;
  const cards = [
    { label: 'Active sessions', value: String(metrics.activeSessions), hint: 'Live active end-user sessions.', href: routeHref('sessions') },
    { label: 'Login failures', value: String(metrics.loginFailures), hint: 'Aggregated auth + admin login failures.', href: routeHref('audit-logs') },
    { label: 'Device mismatches', value: String(metrics.deviceMismatches), hint: 'Mismatch denials detected from the audit stream.', href: routeHref('audit-logs') },
    { label: 'Destructive actions', value: String(metrics.destructiveActions), hint: 'Admin revoke/unbind/disable/rebind/session revoke actions.', href: routeHref('audit-logs') },
  ];
  return `
    <section class="stack">
      <section class="grid">
        ${cards
          .map(
            (metric) => `
              <article class="metric">
                <a href="${metric.href}">
                  <span class="eyebrow">${metric.label}</span>
                  <strong>${metric.value}</strong>
                  <p>${metric.hint}</p>
                </a>
              </article>
            `,
          )
          .join('')}
      </section>
      ${metrics.errorMessage ? renderRetryableError(metrics.errorMessage, 'dashboard-retry') : ''}
      <section class="users-layout">
        <article class="card detail-grid">
          <div class="inline-meta">
            <div>
              <div class="eyebrow">Recent failed events</div>
              <h2>Recent critical events</h2>
            </div>
            <a class="muted-link" href="${routeHref('audit-logs')}">Open audit logs</a>
          </div>
          ${
            metrics.recentFailures.length > 0
              ? renderDashboardAuditSummary(metrics.recentFailures, 'No recent failed events.')
              : '<div class="empty-state">No recent failed events were returned by the current metrics snapshot.</div>'
          }
        </article>
        <article class="card detail-grid">
          <div class="eyebrow">Recent destructive actions</div>
          <h2>Operator follow-up queue</h2>
          ${
            metrics.recentDestructiveActions.length > 0
              ? renderDashboardAuditSummary(metrics.recentDestructiveActions, 'No destructive actions recorded.')
              : '<div class="empty-state">No destructive actions were returned by the current metrics snapshot.</div>'
          }
        </article>
      </section>
      <section class="card placeholder">
        <h2>Dashboard operations snapshot</h2>
        <p>Use the dashboard to spot incident patterns quickly, then drill directly into audit logs or affected control-plane surfaces.</p>
        <ul>
          <li>Current admin: ${escapeHtml(state.session?.user.display_name ?? state.session?.user.username ?? 'admin')}</li>
          <li>Session ID: <code>${escapeHtml(state.session?.session_id ?? '')}</code></li>
          <li>Expires at: ${escapeHtml(state.session?.expires_at ?? '')}</li>
          <li>Last generated: ${escapeHtml(metrics.generatedAt ?? 'n/a')}</li>
        </ul>
      </section>
    </section>
  `;
}

function renderDashboardAuditSummary(items: AdminAuditRecord[], emptyMessage: string): string {
  if (items.length === 0) {
    return `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
  }
  return `
    <div class="summary-list">
      ${items
        .map(
          (item) => `
            <div class="user-card">
              <strong>${escapeHtml(item.event_type)}</strong>
              <span>${escapeHtml(item.created_at)}</span>
              <div class="user-meta">
                <span class="tag">actor:${escapeHtml(item.actor_id ?? 'n/a')}</span>
                <span class="tag">request:${escapeHtml(item.request_id ?? 'n/a')}</span>
                <span class="tag">trace:${escapeHtml(item.trace_id ?? 'n/a')}</span>
              </div>
            </div>
          `,
        )
        .join('')}
    </div>
  `;
}

function renderAuditLogsRoute(state: AppState): string {
  const auditPage = state.auditPage;
  const selectedAudit = selectAuditRecord(auditPage);
  const queryPreview = buildAuditLogQuery(auditPage.filters);
  return `
    <section class="users-layout">
      <article class="card detail-grid">
        <div class="eyebrow">Admin audit API</div>
        <h2>Audit logs</h2>
        <p>Filter operator-visible events by actor, target, session, and time range to isolate the incident you need.</p>
        ${auditPage.errorMessage ? renderRetryableError(auditPage.errorMessage, 'audit-retry') : ''}
        <form id="admin-audit-form" class="detail-grid">
          <div class="filters-grid">
            <label>
              Event type
              <input id="audit-event-type" value="${escapeHtml(auditPage.filters.eventType)}" placeholder="authorization_user_revoked" />
            </label>
            <label>
              Actor id
              <input id="audit-actor-id" value="${escapeHtml(auditPage.filters.actorId)}" placeholder="admin_1" />
            </label>
            <label>
              Target user
              <input id="audit-target-user-id" value="${escapeHtml(auditPage.filters.targetUserId)}" placeholder="1 or admin_1" />
            </label>
            <label>
              Target device
              <input id="audit-target-device-id" value="${escapeHtml(auditPage.filters.targetDeviceId)}" placeholder="device_123" />
            </label>
            <label>
              Target session
              <input id="audit-target-session-id" value="${escapeHtml(auditPage.filters.targetSessionId)}" placeholder="sess_123" />
            </label>
            <label>
              Created from
              <input id="audit-created-from" type="datetime-local" value="${escapeHtml(auditPage.filters.createdFrom)}" />
            </label>
            <label>
              Created to
              <input id="audit-created-to" type="datetime-local" value="${escapeHtml(auditPage.filters.createdTo)}" />
            </label>
            <label>
              Limit
              <input id="audit-limit" type="number" min="1" value="${String(auditPage.filters.limit)}" />
            </label>
            <label>
              Offset
              <input id="audit-offset" type="number" min="0" value="${String(auditPage.filters.offset)}" />
            </label>
          </div>
          <div class="toolbar">
            <button id="audit-refresh" class="primary" type="submit">Refresh audit logs</button>
            <button id="audit-clear" class="secondary" type="button">Clear filters</button>
            <button id="audit-prev-page" class="secondary" type="button" ${auditPage.filters.offset > 0 ? '' : 'disabled'}>Previous page</button>
            <button
              id="audit-next-page"
              class="secondary"
              type="button"
              ${(auditPage.filters.offset + auditPage.items.length) < auditPage.total ? '' : 'disabled'}
            >Next page</button>
          </div>
        </form>
        <div class="inline-meta">
          <p class="hint">Showing ${String(auditPage.items.length)} of ${String(auditPage.total)} filtered audit events.</p>
          ${queryPreview ? `<code data-testid="audit-query-preview">${escapeHtml(queryPreview)}</code>` : ''}
        </div>
        ${auditPage.loading ? '<p>Loading audit logs…</p>' : ''}
        ${!auditPage.loading && !auditPage.errorMessage && auditPage.items.length === 0 ? '<div class="empty-state">No audit events matched the current filters. Adjust the filters or retry the query.</div>' : ''}
        <div class="users-list" data-testid="audit-list">
          ${auditPage.items
            .map(
              (row) => `
                <button class="user-card ${row.id === auditPage.selectedAuditId ? 'active' : ''}" type="button" data-audit-id="${row.id}">
                  <strong>${escapeHtml(row.event_type)}</strong>
                  <span>${escapeHtml(row.created_at)}</span>
                  <div class="user-meta">
                    <span class="tag">actor:${escapeHtml(row.actor_id ?? 'n/a')}</span>
                    <span class="tag">user:${escapeHtml(row.target_user_id ?? 'n/a')}</span>
                    <span class="tag">device:${escapeHtml(row.target_device_id ?? 'n/a')}</span>
                    <span class="tag">session:${escapeHtml(row.target_session_id ?? 'n/a')}</span>
                  </div>
                </button>
              `,
            )
            .join('')}
        </div>
      </article>
      <article class="card detail-grid audit-detail">
        <div class="eyebrow">Selected event</div>
        <h2>${selectedAudit ? escapeHtml(selectedAudit.event_type) : 'Select an audit event'}</h2>
        ${selectedAudit ? renderAuditDetail(selectedAudit) : '<div class="empty-state">Choose an audit event to inspect request tracing and normalized details.</div>'}
      </article>
    </section>
  `;
}

function renderRetryableError(message: string, retryId: string): string {
  return `
    <div class="error">
      <div class="inline-actions">
        <span>${escapeHtml(message)}</span>
        <button id="${retryId}" class="secondary" type="button">Retry</button>
      </div>
    </div>
  `;
}

function selectAuditRecord(auditPage: AuditPageState): AdminAuditRecord | null {
  return auditPage.items.find((row) => row.id === auditPage.selectedAuditId) ?? auditPage.items[0] ?? null;
}

function renderAuditDetail(row: AdminAuditRecord): string {
  return `
    <div class="detail-list" data-testid="audit-detail">
      <div class="user-meta">
        <span class="tag">actor:${escapeHtml(row.actor_id ?? 'n/a')}</span>
        <span class="tag">user:${escapeHtml(row.target_user_id ?? 'n/a')}</span>
        <span class="tag">device:${escapeHtml(row.target_device_id ?? 'n/a')}</span>
        <span class="tag">session:${escapeHtml(row.target_session_id ?? 'n/a')}</span>
      </div>
      <p><strong>Request ID:</strong> ${escapeHtml(row.request_id ?? 'n/a')}</p>
      <p><strong>Trace ID:</strong> ${escapeHtml(row.trace_id ?? 'n/a')}</p>
      <p><strong>Created at:</strong> ${escapeHtml(row.created_at)}</p>
      ${renderAuditDetailEntries(row.details)}
    </div>
  `;
}

function renderAuditDetailEntries(details: Record<string, unknown>): string {
  const entries = Object.entries(details);
  if (entries.length === 0) {
    return '<div class="empty-state">No structured detail payload was attached to this event.</div>';
  }
  const highlightedKeys = ['reason', 'required_permission', 'user_id', 'device_id', 'session_id'];
  const highlighted = entries.filter(([key]) => highlightedKeys.includes(key));
  const remaining = entries.filter(([key]) => !highlightedKeys.includes(key));

  return `
    ${highlighted.length > 0
      ? `<div class="detail-list">
          ${highlighted
            .map(
              ([key, value]) => `
                <p><strong>${escapeHtml(key)}:</strong> ${escapeHtml(formatAuditValue(value))}</p>
              `,
            )
            .join('')}
        </div>`
      : ''}
    ${
      remaining.length > 0
        ? `<pre data-testid="audit-detail-json">${escapeHtml(JSON.stringify(Object.fromEntries(remaining), null, 2))}</pre>`
        : ''
    }
  `;
}

function formatAuditValue(value: unknown): string {
  if (value === null || value === undefined) {
    return 'n/a';
  }
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return JSON.stringify(value);
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
