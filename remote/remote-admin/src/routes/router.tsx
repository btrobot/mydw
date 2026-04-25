import { Button, Result } from 'antd';
import { RouterProvider, createHashRouter, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { AppShell } from '../app/AppShell.js';
import { useAuth } from '../features/auth/auth-context.js';
import { DashboardPage } from '../pages/dashboard/DashboardPage.js';
import { DevicesPage } from '../pages/devices/DevicesPage.js';
import { LoginPage } from '../pages/login/LoginPage.js';
import { SessionsPage } from '../pages/sessions/SessionsPage.js';
import { UsersPage } from '../pages/users/UsersPage.js';
import { LoadingState } from '../components/states/LoadingState.js';

function RootRedirect(): JSX.Element {
  const { status } = useAuth();

  if (status === 'restoring') {
    return <LoadingState title="Restoring admin session" />;
  }

  return <Navigate to={status === 'authenticated' ? '/dashboard' : '/login'} replace />;
}

function ProtectedRoute(): JSX.Element {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'restoring') {
    return <LoadingState title="Checking admin access" />;
  }

  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

function PendingPage(): JSX.Element {
  const navigate = useNavigate();

  return (
    <Result
      status="info"
      title="This page is queued for migration"
      subTitle="Day 3 has migrated users, devices, and sessions into the React shell. Audit remains queued."
      extra={
        <Button type="primary" onClick={() => navigate('/dashboard')}>
          Back to dashboard
        </Button>
      }
    />
  );
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
          { path: '/audit-logs', element: <PendingPage /> },
        ],
      },
    ],
  },
]);

export function AppRouter(): JSX.Element {
  return <RouterProvider router={router} />;
}
