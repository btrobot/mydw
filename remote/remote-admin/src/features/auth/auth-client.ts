export type AdminIdentity = {
  id: string;
  username: string;
  display_name: string;
  role: string;
};

export type AdminSession = {
  session_id: string;
  expires_at: string;
  user: AdminIdentity;
};

export type AdminLoginResponse = {
  access_token: string;
  session_id: string;
  expires_at: string;
  token_type: string;
  user: AdminIdentity;
};

export type DashboardMetrics = {
  active_sessions: number;
  login_failures: number;
  device_mismatches: number;
  destructive_actions: number;
  generated_at: string;
};

export type AdminUserRecord = {
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
};

export type AdminUserListResponse = {
  items: AdminUserRecord[];
  total: number;
};

export type AdminActionResponse = {
  success: boolean;
};

export type AdminUsersFilters = {
  query: string;
  status: string;
  licenseStatus: string;
};

export type AdminDeviceRecord = {
  device_id: string;
  user_id?: string | null;
  device_status: string;
  first_bound_at?: string | null;
  last_seen_at?: string | null;
  client_version?: string | null;
};

export type AdminDeviceListResponse = {
  items: AdminDeviceRecord[];
  total: number;
};

export type AdminDevicesFilters = {
  query: string;
  status: string;
  userId: string;
};

export type AdminDeviceRebindRequest = {
  user_id: string;
  client_version?: string | null;
};

export type AdminSessionRecord = {
  session_id: string;
  user_id?: string | null;
  device_id?: string | null;
  auth_state: string;
  issued_at: string;
  expires_at: string;
  last_seen_at: string;
};

export type AdminSessionListResponse = {
  items: AdminSessionRecord[];
  total: number;
};

export type AdminSessionsFilters = {
  query: string;
  authState: string;
  userId: string;
  deviceId: string;
};

type RemoteAdminWindow = Window & {
  REMOTE_ADMIN_API_BASE?: string;
};

export class AdminApiError extends Error {
  constructor(
    readonly errorCode?: string,
    message = 'Request failed',
    readonly details?: Record<string, unknown>
  ) {
    super(message);
  }
}

export function getApiBase(): string {
  const search = new URLSearchParams(window.location.search);
  const searchBase = search.get('apiBase');
  const configuredBase = (window as RemoteAdminWindow).REMOTE_ADMIN_API_BASE;
  const base = searchBase || configuredBase || 'http://127.0.0.1:8100';
  return base.replace(/\/$/, '');
}

export async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, init);
  const payload = (await response.json()) as Record<string, unknown>;

  if (!response.ok) {
    throw new AdminApiError(
      typeof payload.error_code === 'string' ? payload.error_code : undefined,
      typeof payload.message === 'string' ? payload.message : 'Request failed',
      typeof payload.details === 'object' && payload.details !== null
        ? (payload.details as Record<string, unknown>)
        : undefined
    );
  }

  return payload as T;
}

export async function loginAdmin(username: string, password: string): Promise<AdminLoginResponse> {
  return requestJson<AdminLoginResponse>('/admin/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });
}

export async function getCurrentAdminSession(accessToken: string): Promise<AdminSession> {
  return requestJson<AdminSession>('/admin/session', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getDashboardMetrics(accessToken: string): Promise<DashboardMetrics> {
  return requestJson<DashboardMetrics>('/admin/metrics/summary', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
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
      return 'Unable to sign in right now.';
  }
}

export function mapAdminActionError(errorCode?: string): string {
  switch (errorCode) {
    case 'forbidden':
      return 'Your current role is read-only and cannot perform this action.';
    case 'not_found':
      return 'The requested user could not be found.';
    case 'token_expired':
      return 'Your admin session expired. Please sign in again.';
    default:
      return 'The action failed. Please retry.';
  }
}

export function mapDeviceActionError(errorCode?: string): string {
  switch (errorCode) {
    case 'forbidden':
      return 'Your current role is read-only and cannot perform this device action.';
    case 'not_found':
      return 'The requested device or target user could not be found.';
    case 'token_expired':
      return 'Your admin session expired. Please sign in again.';
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
    case 'token_expired':
      return 'Your admin session expired. Please sign in again.';
    default:
      return 'The session action failed. Please retry.';
  }
}

export function canEditUsersRole(session: AdminSession | null): boolean {
  return session?.user.role === 'super_admin' || session?.user.role === 'auth_admin';
}

export function isAuthExpiredError(errorCode?: string): boolean {
  return errorCode === 'token_expired';
}

export function buildUsersQuery(filters: AdminUsersFilters): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.status) params.set('status', filters.status);
  if (filters.licenseStatus) params.set('license_status', filters.licenseStatus);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function buildDevicesQuery(filters: AdminDevicesFilters): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.status) params.set('device_status', filters.status);
  if (filters.userId) params.set('user_id', filters.userId);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function buildSessionsQuery(filters: AdminSessionsFilters): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.authState) params.set('auth_state', filters.authState);
  if (filters.userId) params.set('user_id', filters.userId);
  if (filters.deviceId) params.set('device_id', filters.deviceId);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export async function getAdminUsers(accessToken: string, filters: AdminUsersFilters): Promise<AdminUserListResponse> {
  return requestJson<AdminUserListResponse>(`/admin/users${buildUsersQuery(filters)}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getAdminUserDetail(accessToken: string, userId: string): Promise<AdminUserRecord> {
  return requestJson<AdminUserRecord>(`/admin/users/${userId}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function revokeAdminUser(accessToken: string, userId: string): Promise<AdminActionResponse> {
  return requestJson<AdminActionResponse>(`/admin/users/${userId}/revoke`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function restoreAdminUser(accessToken: string, userId: string): Promise<AdminActionResponse> {
  return requestJson<AdminActionResponse>(`/admin/users/${userId}/restore`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getAdminDevices(accessToken: string, filters: AdminDevicesFilters): Promise<AdminDeviceListResponse> {
  return requestJson<AdminDeviceListResponse>(`/admin/devices${buildDevicesQuery(filters)}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function getAdminDeviceDetail(accessToken: string, deviceId: string): Promise<AdminDeviceRecord> {
  return requestJson<AdminDeviceRecord>(`/admin/devices/${deviceId}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function unbindAdminDevice(accessToken: string, deviceId: string): Promise<AdminActionResponse> {
  return requestJson<AdminActionResponse>(`/admin/devices/${deviceId}/unbind`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function disableAdminDevice(accessToken: string, deviceId: string): Promise<AdminActionResponse> {
  return requestJson<AdminActionResponse>(`/admin/devices/${deviceId}/disable`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function rebindAdminDevice(
  accessToken: string,
  deviceId: string,
  payload: AdminDeviceRebindRequest
): Promise<AdminActionResponse> {
  return requestJson<AdminActionResponse>(`/admin/devices/${deviceId}/rebind`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function getAdminSessions(accessToken: string, filters: AdminSessionsFilters): Promise<AdminSessionListResponse> {
  return requestJson<AdminSessionListResponse>(`/admin/sessions${buildSessionsQuery(filters)}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function revokeAdminSession(accessToken: string, sessionId: string): Promise<AdminActionResponse> {
  return requestJson<AdminActionResponse>(`/admin/sessions/${sessionId}/revoke`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
