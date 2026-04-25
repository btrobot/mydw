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

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type OffsetPaginationFilters = {
  limit: number;
  offset: number;
};

export const DEFAULT_ADMIN_LIST_PAGE_SIZE = 50;
export const ADMIN_PAGE_SIZE_OPTIONS = [10, 25, 50, 100] as const;

export type AdminUserListResponse = PaginatedResponse<AdminUserRecord>;

export type AdminActionResponse = {
  success: boolean;
};

export type AdminUsersFilters = OffsetPaginationFilters & {
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

export type AdminDeviceListResponse = PaginatedResponse<AdminDeviceRecord>;

export type AdminDevicesFilters = OffsetPaginationFilters & {
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

export type AdminSessionListResponse = PaginatedResponse<AdminSessionRecord>;

export type AdminSessionsFilters = OffsetPaginationFilters & {
  query: string;
  authState: string;
  userId: string;
  deviceId: string;
};

export type AdminAuditRecord = {
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
};

export type AdminAuditListResponse = PaginatedResponse<AdminAuditRecord>;

export type AdminAuditFilters = {
  eventType: string;
  actorId: string;
  targetUserId: string;
  targetDeviceId: string;
  targetSessionId: string;
  createdFrom: string;
  createdTo: string;
  limit: number;
  offset: number;
};

export function formatPageSummary<T>(response: PaginatedResponse<T>): string {
  return `Page ${response.page} · page size ${response.page_size} · total ${response.total}`;
}

export function hasPreviousPage(filters: OffsetPaginationFilters): boolean {
  return filters.offset > 0;
}

export function hasNextPage<T>(response: PaginatedResponse<T> | undefined, filters: OffsetPaginationFilters): boolean {
  if (!response) {
    return false;
  }

  return filters.offset + response.items.length < response.total;
}

export function shiftOffsetPagination<T extends OffsetPaginationFilters>(
  filters: T,
  direction: 'prev' | 'next'
): T {
  const nextOffset =
    direction === 'prev' ? Math.max(0, filters.offset - filters.limit) : filters.offset + filters.limit;

  return {
    ...filters,
    offset: nextOffset,
  };
}

export function replacePaginationPageSize<T extends OffsetPaginationFilters>(filters: T, limit: number): T {
  return {
    ...filters,
    limit,
    offset: 0,
  };
}

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

function appendPaginationQuery(params: URLSearchParams, filters: OffsetPaginationFilters): void {
  params.set('limit', String(filters.limit));
  params.set('offset', String(filters.offset));
}

export function buildUsersQuery(filters: AdminUsersFilters): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.status) params.set('status', filters.status);
  if (filters.licenseStatus) params.set('license_status', filters.licenseStatus);
  appendPaginationQuery(params, filters);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function buildDevicesQuery(filters: AdminDevicesFilters): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.status) params.set('device_status', filters.status);
  if (filters.userId) params.set('user_id', filters.userId);
  appendPaginationQuery(params, filters);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function buildSessionsQuery(filters: AdminSessionsFilters): string {
  const params = new URLSearchParams();
  if (filters.query) params.set('q', filters.query);
  if (filters.authState) params.set('auth_state', filters.authState);
  if (filters.userId) params.set('user_id', filters.userId);
  if (filters.deviceId) params.set('device_id', filters.deviceId);
  appendPaginationQuery(params, filters);
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function toUtcAuditFilterTimestamp(localValue: string, boundary: 'start' | 'end'): string {
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

export function buildAuditLogQuery(filters: AdminAuditFilters): string {
  const params = new URLSearchParams();
  if (filters.eventType) params.set('event_type', filters.eventType);
  if (filters.actorId) params.set('actor_id', filters.actorId);
  if (filters.targetUserId) params.set('target_user_id', filters.targetUserId);
  if (filters.targetDeviceId) params.set('target_device_id', filters.targetDeviceId);
  if (filters.targetSessionId) params.set('target_session_id', filters.targetSessionId);
  if (filters.createdFrom) params.set('created_from', toUtcAuditFilterTimestamp(filters.createdFrom, 'start'));
  if (filters.createdTo) params.set('created_to', toUtcAuditFilterTimestamp(filters.createdTo, 'end'));
  appendPaginationQuery(params, filters);
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

export async function getAdminAuditLogs(accessToken: string, filters: AdminAuditFilters): Promise<AdminAuditListResponse> {
  return requestJson<AdminAuditListResponse>(`/admin/audit-logs${buildAuditLogQuery(filters)}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
