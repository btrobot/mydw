export type AdminAuthStatus = 'restoring' | 'anonymous' | 'authenticated';

export const ADMIN_LOGIN_PATH = '/login';
export const ADMIN_DASHBOARD_PATH = '/dashboard';

export const ADMIN_PAGE_TITLES: Record<string, string> = {
  [ADMIN_DASHBOARD_PATH]: 'Dashboard',
  '/users': 'Users',
  '/devices': 'Devices',
  '/sessions': 'Sessions',
  '/audit-logs': 'Audit Logs',
};

export function resolveRootAdminPath(status: AdminAuthStatus): string {
  return status === 'authenticated' ? ADMIN_DASHBOARD_PATH : ADMIN_LOGIN_PATH;
}

export function resolveProtectedAdminRedirect(status: AdminAuthStatus, pathname: string): string | null {
  if (status === 'restoring') {
    return null;
  }

  if (status === 'authenticated') {
    return pathname === ADMIN_LOGIN_PATH ? ADMIN_DASHBOARD_PATH : null;
  }

  return pathname === ADMIN_LOGIN_PATH ? null : ADMIN_LOGIN_PATH;
}

export function getAdminPageTitle(pathname: string): string {
  return ADMIN_PAGE_TITLES[pathname] ?? 'Remote Admin';
}
