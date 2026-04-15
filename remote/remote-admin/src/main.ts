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
      generated_at: string;
      recent_failures: AdminAuditRecord[];
      recent_destructive_actions: AdminAuditRecord[];
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
          generatedAt: metrics.generated_at,
          recentFailures: metrics.recent_failures,
          recentDestructiveActions: metrics.recent_destructive_actions,
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
    const listing = await request<{ items: AdminUserRecord[]; total: number }>(`/admin/users${buildUsersQuery(state.usersPage.filters)}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const selectedUserId =
      listing.items.find((item) => item.id === state.usersPage.selectedUserId)?.id ??
      listing.items[0]?.id ??
      null;
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        items: listing.items,
        selectedUserId,
        detail: selectedUserId ? state.usersPage.detail : null,
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
    const listing = await request<{ items: AdminDeviceRecord[]; total: number }>(`/admin/devices${buildDevicesQuery(state.devicesPage.filters)}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const selectedDeviceId =
      listing.items.find((item) => item.device_id === state.devicesPage.selectedDeviceId)?.device_id ??
      listing.items[0]?.device_id ??
      null;
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        items: listing.items,
        selectedDeviceId,
        detail: selectedDeviceId ? state.devicesPage.detail : null,
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
    const listing = await request<{ items: AdminSessionRecord[]; total: number }>(`/admin/sessions${buildSessionsQuery(state.sessionsPage.filters)}`, {
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
        selectedSessionId:
          listing.items.find((item) => item.session_id === state.sessionsPage.selectedSessionId)?.session_id ??
          listing.items[0]?.session_id ??
          null,
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
    const suffix = buildAuditLogQuery(state.auditPage.filters);
    const result = await request<{ items: AdminAuditRecord[]; total: number }>(`/admin/audit-logs${suffix}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    state = {
      ...state,
      auditPage: {
        ...state.auditPage,
        items: result.items,
        total: result.total,
        selectedAuditId: result.items[0]?.id ?? null,
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
  bindUsersFilters();
  bindUserCards();
  bindUserForm();
  bindDevicesFilters();
  bindDeviceCards();
  bindDeviceForm();
  bindSessionsFilters();
  bindSessionSelection();
  bindSessionActions();
  bindAuditForm();
  bindAuditCards();
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

function bindUsersFilters(): void {
  const form = document.getElementById('users-filter-form') as HTMLFormElement | null;
  if (!form) {
    return;
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        filters: {
          query: (document.getElementById('users-query') as HTMLInputElement | null)?.value.trim() ?? '',
          status: (document.getElementById('users-status-filter') as HTMLSelectElement | null)?.value ?? '',
          licenseStatus: (document.getElementById('users-license-filter') as HTMLSelectElement | null)?.value ?? '',
        },
      },
    };
    await ensureUsersLoaded();
  });

  const clearButton = document.getElementById('users-filter-clear');
  if (clearButton) {
    clearButton.addEventListener('click', async () => {
      state = {
        ...state,
        usersPage: {
          ...state.usersPage,
          filters: createInitialState('users').usersPage.filters,
        },
      };
      await ensureUsersLoaded();
    });
  }
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

function bindDevicesFilters(): void {
  const form = document.getElementById('devices-filter-form') as HTMLFormElement | null;
  if (!form) {
    return;
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        filters: {
          query: (document.getElementById('devices-query') as HTMLInputElement | null)?.value.trim() ?? '',
          status: (document.getElementById('devices-status-filter') as HTMLSelectElement | null)?.value ?? '',
          userId: (document.getElementById('devices-user-filter') as HTMLInputElement | null)?.value.trim() ?? '',
        },
      },
    };
    await ensureDevicesLoaded();
  });

  const clearButton = document.getElementById('devices-filter-clear');
  if (clearButton) {
    clearButton.addEventListener('click', async () => {
      state = {
        ...state,
        devicesPage: {
          ...state.devicesPage,
          filters: createInitialState('devices').devicesPage.filters,
        },
      };
      await ensureDevicesLoaded();
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

function bindSessionsFilters(): void {
  const form = document.getElementById('sessions-filter-form') as HTMLFormElement | null;
  if (!form) {
    return;
  }
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    state = {
      ...state,
      sessionsPage: {
        ...state.sessionsPage,
        filters: {
          query: (document.getElementById('sessions-query') as HTMLInputElement | null)?.value.trim() ?? '',
          authState: (document.getElementById('sessions-auth-state-filter') as HTMLSelectElement | null)?.value ?? '',
          userId: (document.getElementById('sessions-user-filter') as HTMLInputElement | null)?.value.trim() ?? '',
          deviceId: (document.getElementById('sessions-device-filter') as HTMLInputElement | null)?.value.trim() ?? '',
        },
      },
    };
    await ensureSessionsLoaded();
  });

  const clearButton = document.getElementById('sessions-filter-clear');
  if (clearButton) {
    clearButton.addEventListener('click', async () => {
      state = {
        ...state,
        sessionsPage: {
          ...state.sessionsPage,
          filters: createInitialState('sessions').sessionsPage.filters,
        },
      };
      await ensureSessionsLoaded();
    });
  }
}

function bindSessionSelection(): void {
  for (const element of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-session-select-id]'))) {
    element.addEventListener('click', () => {
      const sessionId = element.dataset.sessionSelectId;
      if (!sessionId) {
        return;
      }
      state = {
        ...state,
        sessionsPage: {
          ...state.sessionsPage,
          selectedSessionId: sessionId,
        },
      };
      render();
    });
  }
}

function bindSessionActions(): void {
  for (const element of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-session-id]'))) {
    element.addEventListener('click', async () => {
      if (!canEditUsers(state.session)) {
        return;
      }
      const sessionId = element.dataset.sessionId;
      if (!sessionId || !confirmAdminAction('sessionRevoke', sessionId)) {
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
    const actorId = (document.getElementById('audit-actor-id') as HTMLInputElement | null)?.value.trim() ?? '';
    const targetUserId = (document.getElementById('audit-target-user-id') as HTMLInputElement | null)?.value.trim() ?? '';
    const targetDeviceId = (document.getElementById('audit-target-device-id') as HTMLInputElement | null)?.value.trim() ?? '';
    const targetSessionId = (document.getElementById('audit-target-session-id') as HTMLInputElement | null)?.value.trim() ?? '';
    const createdFrom = (document.getElementById('audit-created-from') as HTMLInputElement | null)?.value ?? '';
    const createdTo = (document.getElementById('audit-created-to') as HTMLInputElement | null)?.value ?? '';
    const limit = Number((document.getElementById('audit-limit') as HTMLInputElement | null)?.value ?? state.auditPage.filters.limit);
    const offset = Number((document.getElementById('audit-offset') as HTMLInputElement | null)?.value ?? 0);
    state = {
      ...state,
      auditPage: {
        ...state.auditPage,
        filters: {
          eventType,
          actorId,
          targetUserId,
          targetDeviceId,
          targetSessionId,
          createdFrom,
          createdTo,
          limit: Number.isFinite(limit) && limit > 0 ? limit : state.auditPage.filters.limit,
          offset: Number.isFinite(offset) && offset >= 0 ? offset : 0,
        },
      },
    };
    await ensureAuditLogsLoaded();
  });

  const clearButton = document.getElementById('audit-clear');
  if (clearButton) {
    clearButton.addEventListener('click', async () => {
      state = {
        ...state,
        auditPage: {
          ...createInitialState('audit-logs').auditPage,
          items: state.auditPage.items,
        },
      };
      await ensureAuditLogsLoaded();
    });
  }

  const previousPageButton = document.getElementById('audit-prev-page');
  if (previousPageButton) {
    previousPageButton.addEventListener('click', async () => {
      if (state.auditPage.filters.offset <= 0) {
        return;
      }
      state = {
        ...state,
        auditPage: {
          ...state.auditPage,
          filters: {
            ...state.auditPage.filters,
            offset: Math.max(0, state.auditPage.filters.offset - state.auditPage.filters.limit),
          },
        },
      };
      await ensureAuditLogsLoaded();
    });
  }

  const nextPageButton = document.getElementById('audit-next-page');
  if (nextPageButton) {
    nextPageButton.addEventListener('click', async () => {
      if (state.auditPage.filters.offset + state.auditPage.items.length >= state.auditPage.total) {
        return;
      }
      state = {
        ...state,
        auditPage: {
          ...state.auditPage,
          filters: {
            ...state.auditPage.filters,
            offset: state.auditPage.filters.offset + state.auditPage.filters.limit,
          },
        },
      };
      await ensureAuditLogsLoaded();
    });
  }
}

function bindAuditCards(): void {
  for (const element of Array.from(document.querySelectorAll<HTMLButtonElement>('[data-audit-id]'))) {
    element.addEventListener('click', () => {
      const auditId = element.dataset.auditId;
      if (!auditId) {
        return;
      }
      state = {
        ...state,
        auditPage: {
          ...state.auditPage,
          selectedAuditId: auditId,
        },
      };
      render();
    });
  }
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
      await refreshUsersAfterMutation(updated.id, 'User authorization updated.');
    } catch (error) {
      updateUserEditorFailure(error);
    }
  });

  const revokeButton = document.getElementById('user-revoke');
  if (revokeButton) {
    revokeButton.addEventListener('click', async () => {
      const target = state.usersPage.detail;
      if (!target || !canEditUsers(state.session) || !confirmAdminAction('userRevoke', target.id)) {
        return;
      }
      await runUserAction('revoke', 'User authorization revoked.');
    });
  }

  const restoreButton = document.getElementById('user-restore');
  if (restoreButton) {
    restoreButton.addEventListener('click', async () => {
      const target = state.usersPage.detail;
      if (!target || !canEditUsers(state.session) || !confirmAdminAction('userRestore', target.id)) {
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
    await refreshUsersAfterMutation(detail.id, feedback);
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
    if (!detail || !confirmAdminAction('deviceRebind', detail.device_id)) {
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
      await refreshDevicesAfterMutation(detail.device_id, 'Device rebound.');
    } catch (error) {
      updateDeviceEditorFailure(error);
    }
  });

  const unbindButton = document.getElementById('device-unbind');
  if (unbindButton) {
    unbindButton.addEventListener('click', async () => {
      const target = state.devicesPage.detail;
      if (!target || !canEditUsers(state.session) || !confirmAdminAction('deviceUnbind', target.device_id)) {
        return;
      }
      await runDeviceAction('unbind', 'Device unbound.');
    });
  }

  const disableButton = document.getElementById('device-disable');
  if (disableButton) {
    disableButton.addEventListener('click', async () => {
      const target = state.devicesPage.detail;
      if (!target || !canEditUsers(state.session) || !confirmAdminAction('deviceDisable', target.device_id)) {
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
    await refreshDevicesAfterMutation(detail.device_id, feedback);
  } catch (error) {
    updateDeviceEditorFailure(error);
  }
}

async function refreshDevicesAfterMutation(deviceId: string, feedback: string): Promise<void> {
  await ensureDevicesLoaded();
  if (state.devicesPage.selectedDeviceId === deviceId && state.devicesPage.detail) {
    state = {
      ...state,
      devicesPage: {
        ...state.devicesPage,
        editor: {
          ...state.devicesPage.editor,
          saving: false,
          feedback,
          errorMessage: null,
        },
      },
    };
    render();
  }
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

async function refreshUsersAfterMutation(userId: string, feedback: string): Promise<void> {
  await ensureUsersLoaded();
  if (state.usersPage.selectedUserId === userId && state.usersPage.detail) {
    state = {
      ...state,
      usersPage: {
        ...state.usersPage,
        editor: {
          ...state.usersPage.editor,
          saving: false,
          feedback,
          errorMessage: null,
        },
      },
    };
    render();
  }
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
    await ensureSessionsLoaded();
    state = {
      ...state,
      sessionsPage: {
        ...state.sessionsPage,
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

type ConfirmActionKind = 'userRevoke' | 'userRestore' | 'deviceRebind' | 'deviceUnbind' | 'deviceDisable' | 'sessionRevoke';

const CONFIRMATION_COPY: Record<ConfirmActionKind, string> = {
  userRevoke: 'Revoke this user authorization now?',
  userRestore: 'Restore this user authorization now?',
  deviceRebind: 'Rebind this device to the specified user now?',
  deviceUnbind: 'Unbind this device now?',
  deviceDisable: 'Disable this device now?',
  sessionRevoke: 'Revoke this session now?',
};

function confirmAdminAction(kind: ConfirmActionKind, target: string): boolean {
  return window.confirm(`${CONFIRMATION_COPY[kind]}\n\nTarget: ${target}\nThis action is audited.`);
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
