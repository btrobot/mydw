import { App as AntApp, Alert, Button, Card, Collapse, Space, Typography } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { useAuth } from './AuthProvider'
import { getAuthStatusPageCopy, type AuthStatusVariant } from './authErrorHandler'
import { logoutAuth } from './api'
import { useAuthStatus } from './useAuthStatus'

interface AuthStatusPageProps {
  variant: AuthStatusVariant
}

export default function AuthStatusPage({ variant }: AuthStatusPageProps) {
  const { message } = AntApp.useApp()
  const { session, setSession } = useAuth()
  const navigate = useNavigate()
  const [redirectToLogin, setRedirectToLogin] = useState(false)
  const authStatusQuery = useAuthStatus(true)

  const copy = useMemo(() => getAuthStatusPageCopy(variant), [variant])
  const isGraceVariant = variant === 'grace'
  const liveSession = authStatusQuery.data ?? session
  const diagnosticRows = useMemo(() => {
    if (!liveSession) {
      return []
    }

    return [
      liveSession.display_name ? `当前账号：${liveSession.display_name}` : null,
      liveSession.device_id ? `当前设备标识：${liveSession.device_id}` : null,
      liveSession.auth_state ? `当前授权状态：${liveSession.auth_state}` : null,
      liveSession.denial_reason ? `当前受限原因：${liveSession.denial_reason}` : null,
      liveSession.last_verified_at ? `最近校验时间：${liveSession.last_verified_at}` : null,
    ].filter((value): value is string => Boolean(value))
  }, [liveSession])

  const logoutMutation = useMutation({
    mutationFn: logoutAuth,
    onSuccess: (nextSession) => {
      setSession(nextSession)
      setRedirectToLogin(true)
      message.success(isGraceVariant ? '已退出登录' : '请重新登录')
    },
    onError: (error: unknown) => {
      if (error instanceof Error) {
        message.error(error.message)
        return
      }
      message.error('退出登录失败')
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
        title={copy.descriptor.title}
        style={{ width: 560, maxWidth: '100%' }}
        data-testid={`auth-status-${variant}`}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            type={copy.descriptor.severity}
            showIcon
            data-testid="auth-status-primary-alert"
            message={copy.descriptor.title}
            description={copy.descriptor.description}
          />

          {authStatusQuery.isLoading ? (
            <Alert
              type="info"
              showIcon
              data-testid="auth-status-live-loading"
              message={copy.loadingTitle}
              description={copy.loadingDescription}
            />
          ) : null}

          {authStatusQuery.isError ? (
            <Alert
              type="warning"
              showIcon
              data-testid="auth-status-live-error"
              message={copy.refreshErrorTitle}
              description={copy.refreshErrorDescription}
            />
          ) : null}

          <Collapse
            bordered={false}
            size="small"
            items={[
              {
                key: 'diagnostics',
                label: <span data-testid="auth-status-diagnostics-trigger">{copy.diagnosticsLabel}</span>,
                children: (
                  <div data-testid="auth-status-session-meta">
                    <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
                      {copy.diagnosticsDescription}
                    </Typography.Paragraph>
                    {diagnosticRows.length > 0 ? (
                      <Space direction="vertical" size={4}>
                        {diagnosticRows.map((row) => (
                          <Typography.Text key={row} type="secondary">
                            {row}
                          </Typography.Text>
                        ))}
                      </Space>
                    ) : (
                      <Typography.Text type="secondary">{copy.emptyDiagnosticsText}</Typography.Text>
                    )}
                  </div>
                ),
              },
            ]}
          />

          <Space wrap data-testid="auth-status-actions">
            {isGraceVariant ? (
              <>
                <Button type="primary" onClick={() => navigate('/creative/workbench')}>
                  {copy.continueLabel}
                </Button>
                <Button
                  onClick={() => logoutMutation.mutate()}
                  loading={logoutMutation.isPending}
                  data-testid="auth-status-signout-button"
                >
                  {copy.signoutLabel}
                </Button>
              </>
            ) : (
              <Button
                type="primary"
                onClick={() => logoutMutation.mutate()}
                loading={logoutMutation.isPending}
                data-testid="auth-status-signout-button"
              >
                {copy.signoutLabel}
              </Button>
            )}
          </Space>
        </Space>
      </Card>
    </div>
  )
}
