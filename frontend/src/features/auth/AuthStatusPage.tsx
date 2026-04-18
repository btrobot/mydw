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
  const liveDescriptor = useMemo(
    () => getAuthStateDescriptor(authStatusQuery.data ?? session),
    [authStatusQuery.data, session]
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

          {liveDescriptor && (
            <AuthErrorMessage
              descriptor={liveDescriptor}
              onRetry={() => void authStatusQuery.refetch()}
              testId={`auth-status-live-${variant}`}
            />
          )}

          {session && (
            <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
              {session.display_name
                ? `当前账号：${session.display_name}`
                : session.device_id
                  ? `当前设备标识：${session.device_id}`
                  : '当前授权会话需要重新确认。'}
            </Typography.Paragraph>
          )}

          <Space wrap>
            {isGraceVariant ? (
              <>
                <Button type="primary" onClick={() => navigate('/creative/workbench')}>
                  打开作品工作台
                </Button>
                <Button onClick={() => navigate('/dashboard')}>
                  打开运行总览
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
