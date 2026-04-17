import { Alert, Button, Card, Space, Typography, message } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { logoutAuth } from './api'
import { useAuth } from './AuthProvider'
import AuthErrorMessage from './AuthErrorMessage'
import { getAuthStateDescriptor } from './authErrorHandler'
import { useAuthStatus } from './useAuthStatus'

type AuthStatusVariant = 'revoked' | 'device_mismatch' | 'expired' | 'grace'

interface AuthStatusPageProps {
  variant: AuthStatusVariant
}

const STATUS_CONTENT: Record<
  AuthStatusVariant,
  {
    title: string
    description: string
    type: 'warning' | 'error' | 'info'
  }
> = {
  revoked: {
    title: 'Authorization revoked',
    description: 'The remote authorization has been revoked or disabled. Please sign in again to continue using local features.',
    type: 'error',
  },
  device_mismatch: {
    title: 'Device mismatch',
    description: 'This device does not match the remote authorization record. Please sign in again or re-bind this device.',
    type: 'error',
  },
  expired: {
    title: 'Session expired',
    description: 'The local authorization session has expired. Please sign in again.',
    type: 'warning',
  },
  grace: {
    title: 'Offline grace mode',
    description: 'The app is running in restricted mode: existing local data is visible, but high-risk actions and new background tasks are blocked.',
    type: 'info',
  },
}

export default function AuthStatusPage({ variant }: AuthStatusPageProps) {
  const { session, setSession } = useAuth()
  const navigate = useNavigate()
  const [redirectToLogin, setRedirectToLogin] = useState(false)
  const authStatusQuery = useAuthStatus(true)

  const content = useMemo(() => STATUS_CONTENT[variant], [variant])
  const isGraceVariant = variant === 'grace'
  const liveDescriptor = useMemo(
    () => getAuthStateDescriptor(authStatusQuery.data ?? session),
    [authStatusQuery.data, session]
  )

  const logoutMutation = useMutation({
    mutationFn: logoutAuth,
    onSuccess: (nextSession) => {
      setSession(nextSession)
      setRedirectToLogin(true)
      message.success('Signed out')
    },
    onError: (error: unknown) => {
      if (error instanceof Error) {
        message.error(error.message)
        return
      }
      message.error('Failed to sign out')
    },
  })

  if (redirectToLogin) {
    return <Navigate to="/login" replace />
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f2f5',
        padding: 24,
      }}
    >
      <Card
        title={content.title}
        style={{ width: 560, maxWidth: '100%' }}
        data-testid={`auth-status-${variant}`}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            type={content.type}
            showIcon
            message={content.title}
            description={content.description}
          />

          {liveDescriptor && (
            <AuthErrorMessage
              descriptor={liveDescriptor}
              onRetry={() => void authStatusQuery.refetch()}
              testId={`auth-status-live-${variant}`}
            />
          )}

          {session && (
            <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
              State: {session.auth_state}
              {session.display_name ? ` · User: ${session.display_name}` : ''}
              {session.denial_reason ? ` · Reason: ${session.denial_reason}` : ''}
            </Typography.Paragraph>
          )}

          <Space wrap>
            {isGraceVariant ? (
              <>
                <Button type="primary" onClick={() => navigate('/creative/workbench')}>
                  Open creative workbench
                </Button>
                <Button onClick={() => navigate('/dashboard')}>
                  Open runtime dashboard
                </Button>
                <Button
                  onClick={() => logoutMutation.mutate()}
                  loading={logoutMutation.isPending}
                  data-testid="auth-status-signout-button"
                >
                  Sign out
                </Button>
              </>
            ) : (
              <Button
                type="primary"
                onClick={() => logoutMutation.mutate()}
                loading={logoutMutation.isPending}
                data-testid="auth-status-signout-button"
              >
                Sign out and go to login
              </Button>
            )}
          </Space>
        </Space>
      </Card>
    </div>
  )
}
