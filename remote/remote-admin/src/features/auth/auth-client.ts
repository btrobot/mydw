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
