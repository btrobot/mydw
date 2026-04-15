import {
  canEditUsers,
  createDeviceEditor,
  createInitialState,
  createUserEditor,
  mapAdminActionError,
  mapDeviceActionError,
  mapLoginError,
  mapSessionActionError,
  normalizeHash,
  renderApp,
  resolveGuardedRoute,
  routeHref,
  type AdminAuditRecord,
  type DashboardMetricsState,
  type AdminSessionRecord,
  type AdminSession,
  type AdminDeviceRecord,
  type AdminUserRecord,
  type AppState,
} from './app/App.js';

const ACCESS_TOKEN_KEY = 'remote_admin_access_token';
const DEFAULT_API_BASE = 'http://127.0.0.1:8100';

type RemoteAdminWindow = Window & {
  REMOTE_ADMIN_API_BASE?: string;
};

const root = getRootElement();

let state: AppState = createInitialState(normalizeHash(window.location.hash));

async function bootstrap(): Promise<void> {
  window.addEventListener('hashchange', async () => {
    state = { ...state, route: normalizeHash(window.location.hash), globalError: null };
    await ensureRouteState();
  });
  await ensureRouteState();
}

async function ensureRouteState(): Promise<void> {
  const guarded = resolveGuardedRoute(state.route, Boolean(state.session));
  if (guarded.redirectTo) {
    redirect(guarded.redirectTo);
    return;
  }
  if (state.route !== 'login' && getStoredAccessToken()) {
    await restoreAdminSession();
    return;
  }
  if (state.route === 'login' && getStoredAccessToken() && !state.session) {
    await restoreAdminSession();
    return;
  }
  await hydrateRoute();
}

async function restoreAdminSession(): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    if (state.route !== 'login') {
      redirect(routeHref('login'));
      return;
    }
    render();
    return;
  }

  state = { ...state, status: 'loading' };
  render();
  try {
    const session = await request<AdminSession>('/admin/session', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    state = { ...state, session, status: 'ready', globalError: null };
    const guarded = resolveGuardedRoute(state.route, true);
    if (guarded.redirectTo) {
      redirect(guarded.redirectTo);
      return;
    }
    await hydrateRoute();
  } catch {
    clearStoredAccessToken();
    state = { ...state, session: null, status: 'ready', globalError: state.route === 'login' ? null : 'The admin session expired. Please sign in again.' };
    if (state.route !== 'login') {
      redirect(routeHref('login'));
      return;
    }
    render();
  }
}

async function hydrateRoute(): Promise<void> {
  if (state.route === 'dashboard' && state.session) {
    await ensureDashboardMetricsLoaded();
    return;
  }
  if (state.route === 'users' && state.session) {
    await ensureUsersLoaded();
    return;
  }
  if (state.route === 'devices' && state.session) {
    await ensureDevicesLoaded();
    return;
  }
  if (state.route === 'sessions' && state.session) {
    await ensureSessionsLoaded();
    return;
  }
  if (state.route === 'audit-logs' && state.session) {
    await ensureAuditLogsLoaded();
    return;
  }
  render();
}

async function ensureDashboardMetricsLoaded(): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    render();
    return;
  }
  state = {
    ...state,
    dashboardMetrics: {
      ...state.dashboardMetrics,
      loading: true,
      errorMessage: null,
    },
  };
  render();
  try {
    const metrics = await request<{
      active_sessions: number;
      login_failures: number;
      device_mismatches: number;
      destructive_actions: number;
    }>('/admin/metrics/summary', {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    state = {
      ...state,
      dashboardMetrics: {
        activeSessions: metrics.active_sessions,
        loginFailures: metrics.login_failures,
        deviceMismatches: metrics.device_mismatches,
        destructiveActions: metrics.destructive_actions,
        loading: false,
        errorMessage: null,
      },
    };
  } catch (error) {
    state = {
      ...state,
      dashboardMetrics: {
        ...state.dashboardMetrics,
        loading: false,
        errorMessage: error instanceof ApiError ? mapAdminActionError(error.errorCode) : 'Failed to load dashboard metrics.',
      },
    };
  }
  render();
}

async function ensureUsersLoaded(): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    render();
    return;
  }
  state = {
    ...state,
    usersPage: {
      ...state.usersPage,
      loading: state.usersPage.items.length === 0,
      errorMessage: null,
    },
  };
  render();
  try {
    const listing = await request<{ items: AdminUserRecord[]; total: number }>('/admin/users', {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const selectedUserId = state.usersPage.selectedUserId ?? listing.items[0]?.id ?? null;
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        items: listing.items,
        selectedUserId,
        loading: false,
        errorMessage: null,
      },
    };
    if (selectedUserId) {
      await loadUserDetail(selectedUserId);
      return;
    }
  } catch (error) {
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        loading: false,
        errorMessage: error instanceof ApiError ? mapAdminActionError(error.errorCode) : 'Failed to load admin users.',
      },
    };
  }
  render();
}

async function loadUserDetail(userId: string): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    return;
  }
  state = {
    ...state,
    usersPage: {
      ...state.usersPage,
      selectedUserId: userId,
      detailLoading: true,
      editor: {
        ...state.usersPage.editor,
        feedback: null,
        errorMessage: null,
      },
    },
  };
  render();
  try {
    const detail = await request<AdminUserRecord>(`/admin/users/${userId}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        selectedUserId: userId,
        detail,
        detailLoading: false,
        editor: createUserEditor(detail),
      },
    };
  } catch (error) {
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        detailLoading: false,
        errorMessage: error instanceof ApiError ? mapAdminActionError(error.errorCode) : 'Failed to load the selected user.',
      },
    };
  }
  render();
}

async function ensureDevicesLoaded(): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    render();
    return;
  }
  state = {
    ...state,
    devicesPage: {
      ...state.devicesPage,
      loading: state.devicesPage.items.length === 0,
      errorMessage: null,
    },
  };
  render();
  try {
    const listing = await request<{ items: AdminDeviceRecord[]; total: number }>('/admin/devices', {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const selectedDeviceId = state.devicesPage.selectedDeviceId ?? listing.items[0]?.device_id ?? null;
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        items: listing.items,
        selectedDeviceId,
        loading: false,
        errorMessage: null,
      },
    };
    if (selectedDeviceId) {
      await loadDeviceDetail(selectedDeviceId);
      return;
    }
  } catch (error) {
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        loading: false,
        errorMessage: error instanceof ApiError ? mapDeviceActionError(error.errorCode) : 'Failed to load devices.',
      },
    };
  }
  render();
}

async function loadDeviceDetail(deviceId: string): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    return;
  }
  state = {
    ...state,
    devicesPage: {
      ...state.devicesPage,
      selectedDeviceId: deviceId,
      detailLoading: true,
      editor: {
        ...state.devicesPage.editor,
        feedback: null,
        errorMessage: null,
      },
    },
  };
  render();
  try {
    const detail = await request<AdminDeviceRecord>(`/admin/devices/${deviceId}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        selectedDeviceId: deviceId,
        detail,
        detailLoading: false,
        editor: createDeviceEditor(detail),
      },
    };
  } catch (error) {
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        detailLoading: false,
        errorMessage: error instanceof ApiError ? mapDeviceActionError(error.errorCode) : 'Failed to load the selected device.',
      },
    };
  }
  render();
}

async function ensureSessionsLoaded(): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    render();
    return;
  }
  state = {
    ...state,
    sessionsPage: {
      ...state.sessionsPage,
      loading: true,
      errorMessage: null,
      feedback: null,
    },
  };
  render();
  try {
    const listing = await request<{ items: AdminSessionRecord[]; total: number }>('/admin/sessions', {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    state = {
      ...state,
      sessionsPage: {
        ...state.sessionsPage,
        items: listing.items,
        loading: false,
        errorMessage: null,
        selectedSessionId: listing.items[0]?.session_id ?? null,
      },
    };
  } catch (error) {
    state = {
      ...state,
      sessionsPage: {
        ...state.sessionsPage,
        loading: false,
        errorMessage: error instanceof ApiError ? mapSessionActionError(error.errorCode) : 'Failed to load sessions.',
      },
    };
  }
  render();
}

async function ensureAuditLogsLoaded(): Promise<void> {
  const accessToken = getStoredAccessToken();
  if (!accessToken) {
    render();
    return;
  }
  state = {
    ...state,
    auditPage: {
      ...state.auditPage,
      loading: true,
      errorMessage: null,
    },
  };
  render();
  try {
    const query = new URLSearchParams();
    if (state.auditPage.filterEventType.trim()) {
      query.set('event_type', state.auditPage.filterEventType.trim());
    }
    const suffix = query.toString() ? `?${query.toString()}` : '';
    const result = await request<{ items: AdminAuditRecord[]; total: number }>(`/admin/audit-logs${suffix}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    state = {
      ...state,
      auditPage: {
        ...state.auditPage,
        items: result.items,
        loading: false,
        errorMessage: null,
      },
    };
  } catch (error) {
    state = {
      ...state,
      auditPage: {
        ...state.auditPage,
        loading: false,
        errorMessage: error instanceof ApiError ? mapAdminActionError(error.errorCode) : 'Failed to load audit logs.',
      },
    };
  }
  render();
}

function render(): void {
  root.innerHTML = renderApp(state);
  bindLoginForm();
  bindLogout();
  bindUserCards();
  bindUserForm();
  bindDeviceCards();
  bindDeviceForm();
  bindSessionCards();
  bindAuditForm();
}

function bindLoginForm(): void {
  const form = document.getElementById('admin-login-form') as HTMLFormElement | null;
  if (!form) {
    return;
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const usernameInput = document.getElementById('admin-username') as HTMLInputElement | null;
    const passwordInput = document.getElementById('admin-password') as HTMLInputElement | null;
    const username = usernameInput?.value.trim() ?? '';
    const password = passwordInput?.value ?? '';
    state = {
      ...state,
      loginForm: {
        username,
        password,
        submitting: true,
        errorMessage: null,
      },
      globalError: null,
    };
    render();
    try {
      const response = await request<{
        access_token: string;
        session_id: string;
        expires_at: string;
        user: AdminSession['user'];
      }>('/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      setStoredAccessToken(response.access_token);
      state = {
        ...state,
        session: {
          session_id: response.session_id,
          expires_at: response.expires_at,
          user: response.user,
        },
        status: 'ready',
        loginForm: {
          username,
          password: '',
          submitting: false,
          errorMessage: null,
        },
      };
      redirect(routeHref('dashboard'));
    } catch (error) {
      const message = error instanceof ApiError ? mapLoginError(error.errorCode) : mapLoginError();
      state = {
        ...state,
        session: null,
        status: 'ready',
        loginForm: {
          username,
          password: '',
          submitting: false,
          errorMessage: message,
        },
      };
      render();
    }
  });
}

function bindLogout(): void {
  const button = document.getElementById('admin-logout');
  if (!button) {
    return;
  }
  button.addEventListener('click', () => {
    clearStoredAccessToken();
    state = createInitialState('login');
    redirect(routeHref('login'));
  });
}

function bindUserCards(): void {
  for (const element of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-user-id]'))) {
    element.addEventListener('click', async () => {
      const userId = element.dataset.userId;
      if (!userId || userId === state.usersPage.selectedUserId) {
        return;
      }
      await loadUserDetail(userId);
    });
  }
}

function bindDeviceCards(): void {
  for (const element of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-device-id]'))) {
    element.addEventListener('click', async () => {
      const deviceId = element.dataset.deviceId;
      if (!deviceId || deviceId === state.devicesPage.selectedDeviceId) {
        return;
      }
      await loadDeviceDetail(deviceId);
    });
  }
}

function bindSessionCards(): void {
  for (const element of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-session-id]'))) {
    element.addEventListener('click', async () => {
      if (!canEditUsers(state.session)) {
        return;
      }
      const sessionId = element.dataset.sessionId;
      if (!sessionId || !window.confirm('Revoke this session now?')) {
        return;
      }
      await runSessionRevoke(sessionId);
    });
  }
}

function bindAuditForm(): void {
  const form = document.getElementById('admin-audit-form') as HTMLFormElement | null;
  if (!form) {
    return;
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const eventType = (document.getElementById('audit-event-type') as HTMLInputElement | null)?.value.trim() ?? '';
    state = {
      ...state,
      auditPage: {
        ...state.auditPage,
        filterEventType: eventType,
      },
    };
    await ensureAuditLogsLoaded();
  });
}

function bindUserForm(): void {
  const form = document.getElementById('admin-user-form') as HTMLFormElement | null;
  if (!form || !state.usersPage.detail || !state.session) {
    return;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!canEditUsers(state.session)) {
      return;
    }
    const detail = state.usersPage.detail;
    if (!detail) {
      return;
    }
    const payload = readUserEditorPayload();
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        editor: {
          ...state.usersPage.editor,
          saving: true,
          feedback: null,
          errorMessage: null,
        },
      },
    };
    render();
    try {
      const updated = await request<AdminUserRecord>(`/admin/users/${detail.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getStoredAccessToken()}`,
        },
        body: JSON.stringify(payload),
      });
      applyUpdatedUser(updated, 'User authorization updated.');
    } catch (error) {
      updateUserEditorFailure(error);
    }
  });

  const revokeButton = document.getElementById('user-revoke');
  if (revokeButton) {
    revokeButton.addEventListener('click', async () => {
      if (!canEditUsers(state.session) || !window.confirm('Revoke this user authorization now?')) {
        return;
      }
      await runUserAction('revoke', 'User authorization revoked.');
    });
  }

  const restoreButton = document.getElementById('user-restore');
  if (restoreButton) {
    restoreButton.addEventListener('click', async () => {
      if (!canEditUsers(state.session) || !window.confirm('Restore this user authorization now?')) {
        return;
      }
      await runUserAction('restore', 'User authorization restored.');
    });
  }
}

async function runUserAction(action: 'revoke' | 'restore', feedback: string): Promise<void> {
  const detail = state.usersPage.detail;
  if (!detail) {
    return;
  }
  try {
    await request(`/admin/users/${detail.id}/${action}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getStoredAccessToken()}`,
      },
    });
    const refreshed = await request<AdminUserRecord>(`/admin/users/${detail.id}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${getStoredAccessToken()}`,
      },
    });
    applyUpdatedUser(refreshed, feedback);
  } catch (error) {
    updateUserEditorFailure(error);
  }
}

function bindDeviceForm(): void {
  const form = document.getElementById('admin-device-form') as HTMLFormElement | null;
  if (!form || !state.devicesPage.detail || !state.session) {
    return;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!canEditUsers(state.session)) {
      return;
    }
    const detail = state.devicesPage.detail;
    if (!detail || !window.confirm('Rebind this device to the specified user now?')) {
      return;
    }
    const payload = readDeviceEditorPayload();
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        editor: {
          ...state.devicesPage.editor,
          saving: true,
          feedback: null,
          errorMessage: null,
        },
      },
    };
    render();
    try {
      await request(`/admin/devices/${detail.device_id}/rebind`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getStoredAccessToken()}`,
        },
        body: JSON.stringify(payload),
      });
      const refreshed = await request<AdminDeviceRecord>(`/admin/devices/${detail.device_id}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${getStoredAccessToken()}`,
        },
      });
      applyUpdatedDevice(refreshed, 'Device rebound.');
    } catch (error) {
      updateDeviceEditorFailure(error);
    }
  });

  const unbindButton = document.getElementById('device-unbind');
  if (unbindButton) {
    unbindButton.addEventListener('click', async () => {
      if (!canEditUsers(state.session) || !window.confirm('Unbind this device now?')) {
        return;
      }
      await runDeviceAction('unbind', 'Device unbound.');
    });
  }

  const disableButton = document.getElementById('device-disable');
  if (disableButton) {
    disableButton.addEventListener('click', async () => {
      if (!canEditUsers(state.session) || !window.confirm('Disable this device now?')) {
        return;
      }
      await runDeviceAction('disable', 'Device disabled.');
    });
  }
}

async function runDeviceAction(action: 'unbind' | 'disable', feedback: string): Promise<void> {
  const detail = state.devicesPage.detail;
  if (!detail) {
    return;
  }
  try {
    await request(`/admin/devices/${detail.device_id}/${action}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getStoredAccessToken()}`,
      },
    });
    const refreshed = await request<AdminDeviceRecord>(`/admin/devices/${detail.device_id}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${getStoredAccessToken()}`,
      },
    });
    applyUpdatedDevice(refreshed, feedback);
  } catch (error) {
    updateDeviceEditorFailure(error);
  }
}

function applyUpdatedDevice(updated: AdminDeviceRecord, feedback: string): void {
  state = {
    ...state,
    devicesPage: {
      ...state.devicesPage,
      items: state.devicesPage.items.map((item) => (item.device_id === updated.device_id ? updated : item)),
      detail: updated,
      editor: {
        ...createDeviceEditor(updated),
        feedback,
      },
    },
  };
  render();
}

function updateDeviceEditorFailure(error: unknown): void {
  state = {
    ...state,
    devicesPage: {
      ...state.devicesPage,
      editor: {
        ...state.devicesPage.editor,
        saving: false,
        feedback: null,
        errorMessage: error instanceof ApiError ? mapDeviceActionError(error.errorCode) : 'The device action failed.',
      },
    },
  };
  render();
}

function applyUpdatedUser(updated: AdminUserRecord, feedback: string): void {
  state = {
    ...state,
    usersPage: {
      ...state.usersPage,
      items: state.usersPage.items.map((item) => (item.id === updated.id ? updated : item)),
      detail: updated,
      editor: {
        ...createUserEditor(updated),
        feedback,
      },
    },
  };
  render();
}

function updateUserEditorFailure(error: unknown): void {
  state = {
    ...state,
    usersPage: {
      ...state.usersPage,
      editor: {
        ...state.usersPage.editor,
        saving: false,
        feedback: null,
        errorMessage: error instanceof ApiError ? mapAdminActionError(error.errorCode) : 'The user action failed.',
      },
    },
  };
  render();
}

function readUserEditorPayload(): Record<string, unknown> {
  const displayName = (document.getElementById('user-display-name') as HTMLInputElement | null)?.value.trim() ?? '';
  const licenseStatus = (document.getElementById('user-license-status') as HTMLSelectElement | null)?.value ?? 'active';
  const licenseExpiresAt = (document.getElementById('user-license-expires-at') as HTMLInputElement | null)?.value ?? '';
  const entitlementsCsv = (document.getElementById('user-entitlements') as HTMLTextAreaElement | null)?.value ?? '';
  const entitlements = entitlementsCsv
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);

  return {
    display_name: displayName || null,
    license_status: licenseStatus,
    license_expires_at: licenseExpiresAt ? new Date(licenseExpiresAt).toISOString() : null,
    entitlements,
  };
}

function readDeviceEditorPayload(): Record<string, unknown> {
  const userId = (document.getElementById('device-rebind-user-id') as HTMLInputElement | null)?.value.trim() ?? '';
  const clientVersion = (document.getElementById('device-rebind-client-version') as HTMLInputElement | null)?.value.trim() ?? '';
  return {
    user_id: userId,
    client_version: clientVersion || null,
  };
}

async function runSessionRevoke(sessionId: string): Promise<void> {
  try {
    await request(`/admin/sessions/${sessionId}/revoke`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getStoredAccessToken()}`,
      },
    });
    state = {
      ...state,
      sessionsPage: {
        ...state.sessionsPage,
        items: state.sessionsPage.items.map((item) =>
          item.session_id === sessionId ? { ...item, auth_state: 'revoked:admin_session_revoked' } : item,
        ),
        selectedSessionId: sessionId,
        feedback: 'Session revoked.',
        errorMessage: null,
      },
    };
  } catch (error) {
    state = {
      ...state,
      sessionsPage: {
        ...state.sessionsPage,
        feedback: null,
        errorMessage: error instanceof ApiError ? mapSessionActionError(error.errorCode) : 'The session action failed.',
      },
    };
  }
  render();
}

function redirect(hash: string): void {
  if (window.location.hash !== hash) {
    window.location.hash = hash;
    return;
  }
  state = { ...state, route: normalizeHash(hash) };
  void hydrateRoute();
}

function getStoredAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function setStoredAccessToken(value: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, value);
}

function clearStoredAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

function getRootElement(): HTMLElement {
  const element = document.getElementById('app');
  if (!element) {
    throw new Error('Missing #app root element for remote-admin');
  }
  return element;
}

class ApiError extends Error {
  constructor(readonly errorCode?: string, message = 'Request failed') {
    super(message);
  }
}

async function request<T = Record<string, unknown>>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, init);
  const payload = (await response.json()) as Record<string, unknown>;
  if (!response.ok) {
    throw new ApiError(typeof payload.error_code === 'string' ? payload.error_code : undefined, typeof payload.message === 'string' ? payload.message : 'Request failed');
  }
  return payload as T;
}

function getApiBase(): string {
  const search = new URLSearchParams(window.location.search);
  const searchBase = search.get('apiBase');
  const configuredBase = (window as RemoteAdminWindow).REMOTE_ADMIN_API_BASE;
  const base = searchBase || configuredBase || DEFAULT_API_BASE;
  return base.replace(/\/$/, '');
}

void bootstrap();
