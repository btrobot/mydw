import { App as AntApp, Alert, Button, Card, Collapse, Space, Typography } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import AuthErrorMessage from './AuthErrorMessage'
import { useAuth } from './AuthProvider'
import { getAuthStateDescriptor } from './authErrorHandler'
import { logoutAuth } from './api'
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
    title: '访问权限已失效',
    description: '当前账号的应用访问权限已失效，请联系管理员恢复权限后再登录。',
    type: 'error',
  },
  device_mismatch: {
    title: '当前设备未通过校验',
    description: '请退出后重新登录；若问题持续，请联系管理员重新绑定设备。',
    type: 'error',
  },
  expired: {
    title: '登录已过期',
    description: '当前登录已过期，请重新登录继续使用。',
    type: 'warning',
  },
  grace: {
    title: '宽限模式',
    description: '当前网络或授权服务暂不可用，你仍可查看已有内容，但受保护操作会受限。',
    type: 'info',
  },
}

export default function AuthStatusPage({ variant }: AuthStatusPageProps) {
  const { message } = AntApp.useApp()
  const { session, setSession } = useAuth()
  const navigate = useNavigate()
  const [redirectToLogin, setRedirectToLogin] = useState(false)
  const authStatusQuery = useAuthStatus(true)

  const content = useMemo(() => STATUS_CONTENT[variant], [variant])
  const isGraceVariant = variant === 'grace'
  const liveSession = authStatusQuery.data ?? session
  const liveDescriptor = useMemo(
    () => getAuthStateDescriptor(liveSession),
    [liveSession],
  )
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
      message.success('已退出登录')
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
        title={content.title}
        style={{ width: 560, maxWidth: '100%' }}
        data-testid={`auth-status-${variant}`}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Alert
            type={content.type}
            showIcon
            data-testid="auth-status-primary-alert"
            message={content.title}
            description={content.description}
          />

          {authStatusQuery.isLoading ? (
            <Alert
              type="info"
              showIcon
              message="正在刷新授权状态"
              description="正在同步最新设备授权结果，请稍候。"
            />
          ) : null}

          {authStatusQuery.isError && !liveDescriptor ? (
            <Alert
              type="warning"
              showIcon
              message="授权状态暂时无法刷新"
              description="当前页面保留最近一次会话信息，请稍后重试。"
            />
          ) : null}

          {liveDescriptor && (
            <AuthErrorMessage
              descriptor={liveDescriptor}
              label="实时状态补充"
              testId={`auth-status-live-${variant}`}
            />
          )}

          <Collapse
            bordered={false}
            size="small"
            items={[
              {
                key: 'diagnostics',
                label: <span data-testid="auth-status-diagnostics-trigger">查看会话与诊断信息</span>,
                children: (
                  <div data-testid="auth-status-session-meta">
                    <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
                      以下信息仅用于说明当前设备会话状态，不影响下方主操作路径。
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
                      <Typography.Text type="secondary">当前授权会话需要重新确认。</Typography.Text>
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
                  继续进入工作台
                </Button>
                <Button
                  onClick={() => logoutMutation.mutate()}
                  loading={logoutMutation.isPending}
                  data-testid="auth-status-signout-button"
                >
                  退出登录并返回登录页
                </Button>
              </>
            ) : (
              <Button
                type="primary"
                onClick={() => logoutMutation.mutate()}
                loading={logoutMutation.isPending}
                data-testid="auth-status-signout-button"
              >
                退出登录并返回登录页
              </Button>
            )}
          </Space>
        </Space>
      </Card>
    </div>
  )
}
