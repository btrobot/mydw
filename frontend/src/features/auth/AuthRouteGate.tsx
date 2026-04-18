import { Alert } from 'antd'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import LayoutComponent from '@/components/Layout'

import { useAuth } from './AuthProvider'

const GraceBanner = () => (
  <div style={{ padding: '16px 16px 0' }} data-testid="auth-grace-banner">
    <Alert
      type="warning"
      showIcon
      message="当前处于离线宽限模式"
      description="你仍可查看现有本地数据，但高风险操作会继续受限。"
    />
  </div>
)

const canAccessGraceShell = (pathname: string) => (
  pathname === '/'
  || pathname === '/dashboard'
  || pathname === '/creative'
  || pathname === '/creative/workbench'
)

export const ProtectedAppShell = () => {
  const { authState } = useAuth()
  const location = useLocation()

  if (authState === 'authenticated_active') {
    return <LayoutComponent />
  }

  if (authState === 'authenticated_grace') {
    if (canAccessGraceShell(location.pathname)) {
      return (
        <>
          <GraceBanner />
          <LayoutComponent />
        </>
      )
    }
    return <Navigate to="/auth/grace" replace state={{ from: location }} />
  }

  if (authState === 'revoked') {
    return <Navigate to="/auth/revoked" replace state={{ from: location }} />
  }

  if (authState === 'device_mismatch') {
    return <Navigate to="/auth/device-mismatch" replace state={{ from: location }} />
  }

  if (authState === 'expired') {
    return <Navigate to="/auth/expired" replace state={{ from: location }} />
  }

  return <Navigate to="/login" replace state={{ from: location }} />
}

export const PublicLoginRoute = () => {
  const { authState } = useAuth()

  if (authState === 'authenticated_active') {
    return <Navigate to="/creative/workbench" replace />
  }

  if (authState === 'authenticated_grace') {
    return <Navigate to="/creative/workbench" replace />
  }

  if (authState === 'revoked') {
    return <Navigate to="/auth/revoked" replace />
  }

  if (authState === 'device_mismatch') {
    return <Navigate to="/auth/device-mismatch" replace />
  }

  if (authState === 'expired') {
    return <Navigate to="/auth/expired" replace />
  }

  return <Outlet />
}
