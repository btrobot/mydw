import { Alert, Button, Card, Space, Typography, message } from 'antd'
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
    title: '授权已失效',
    description: '远端授权已被撤销或停用，请重新登录后继续使用本地能力。',
    type: 'error',
  },
  device_mismatch: {
    title: '设备授权不匹配',
    description: '当前设备与远端授权记录不一致，请重新登录或重新绑定设备。',
    type: 'error',
  },
  expired: {
    title: '登录已过期',
    description: '当前本地授权会话已过期，请重新登录。',
    type: 'warning',
  },
  grace: {
    title: '离线宽限模式',
    description: '当前处于受限模式：你仍可查看已有本地数据，但高风险操作和新的后台任务会被阻止。',
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
  const liveSession = authStatusQuery.data ?? session
  const liveDescriptor = useMemo(
    () => getAuthStateDescriptor(liveSession),
    [liveSession],
  )

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
              action={<Button size="small" onClick={() => void authStatusQuery.refetch()}>重试</Button>}
            />
          ) : null}

          {liveDescriptor && (
            <AuthErrorMessage
              descriptor={liveDescriptor}
              onRetry={() => void authStatusQuery.refetch()}
              testId={`auth-status-live-${variant}`}
            />
          )}

          {liveSession ? (
            <div data-testid="auth-status-session-meta">
              <Typography.Paragraph type="secondary" style={{ marginBottom: 4 }}>
                以下信息仅用于说明当前设备会话状态，主操作请使用下方入口。
              </Typography.Paragraph>
              {liveSession.display_name ? (
                <Typography.Text type="secondary">当前账号：{liveSession.display_name}</Typography.Text>
              ) : liveSession.device_id ? (
                <Typography.Text type="secondary">当前设备标识：{liveSession.device_id}</Typography.Text>
              ) : (
                <Typography.Text type="secondary">当前授权会话需要重新确认。</Typography.Text>
              )}
            </div>
          ) : null}

          <Space wrap>
            {isGraceVariant ? (
              <>
                <Button type="primary" onClick={() => navigate('/creative/workbench')}>
                  继续进入作品工作台
                </Button>
                <Button onClick={() => navigate('/dashboard')}>
                  查看运行总览
                </Button>
                <Button
                  onClick={() => logoutMutation.mutate()}
                  loading={logoutMutation.isPending}
                  data-testid="auth-status-signout-button"
                >
                  退出登录
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
