import { RouterProvider, createHashRouter, Navigate, Outlet, useLocation } from 'react-router-dom';

import { AppShell } from '../app/AppShell.js';
import { AuditLogsPage } from '../pages/audit/AuditLogsPage.js';
import { useAuth } from '../features/auth/auth-context.js';
import { DashboardPage } from '../pages/dashboard/DashboardPage.js';
import { DevicesPage } from '../pages/devices/DevicesPage.js';
import { LoginPage } from '../pages/login/LoginPage.js';
import { SessionsPage } from '../pages/sessions/SessionsPage.js';
import { UsersPage } from '../pages/users/UsersPage.js';
import { LoadingState } from '../components/states/LoadingState.js';
import { resolveProtectedAdminRedirect, resolveRootAdminPath } from './route-helpers.js';

function RootRedirect(): JSX.Element {
  const { status } = useAuth();

  if (status === 'restoring') {
    return <LoadingState title="Restoring admin session" />;
  }

  return <Navigate to={resolveRootAdminPath(status)} replace />;
}

function ProtectedRoute(): JSX.Element {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'restoring') {
    return <LoadingState title="Checking admin access" />;
  }

  const redirectTo = resolveProtectedAdminRedirect(status, location.pathname);
  if (redirectTo) {
    return <Navigate to={redirectTo} replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

const router = createHashRouter([
  { path: '/', element: <RootRedirect /> },
  { path: '/login', element: <LoginPage /> },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: '/dashboard', element: <DashboardPage /> },
          { path: '/users', element: <UsersPage /> },
          { path: '/devices', element: <DevicesPage /> },
          { path: '/sessions', element: <SessionsPage /> },
          { path: '/audit-logs', element: <AuditLogsPage /> },
        ],
      },
    ],
  },
]);

export function AppRouter(): JSX.Element {
  return <RouterProvider router={router} />;
}
