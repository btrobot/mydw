import { App as AntApp, Button, Space, Tag, Typography } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { logoutAuth } from './api'
import { useAuth } from './AuthProvider'
import { AUTH_HEADER_COPY, getAuthStatusTagMeta } from './authErrorHandler'

const { Text } = Typography

export default function AuthSessionHeader() {
  const { message } = AntApp.useApp()
  const { session, authState, setSession } = useAuth()
  const navigate = useNavigate()

  const logoutMutation = useMutation({
    mutationFn: logoutAuth,
    onSuccess: (nextSession) => {
      setSession(nextSession)
      message.success('已退出登录')
      navigate('/login', { replace: true })
    },
    onError: (error: unknown) => {
      if (error instanceof Error) {
        message.error(error.message)
        return
      }
      message.error('退出登录失败')
    },
  })

  const meta = useMemo(
    () => getAuthStatusTagMeta(authState),
    [authState]
  )

  return (
    <Space data-testid="auth-session-header">
      {session?.display_name && <Text style={{ color: 'white' }}>{session.display_name}</Text>}
      <Tag color={meta.color} data-testid="auth-session-status-tag">{meta.label}</Tag>
      {authState !== 'unauthenticated' && (
        <Button
          size="small"
          onClick={() => logoutMutation.mutate()}
          loading={logoutMutation.isPending}
          data-testid="auth-logout-button"
        >
          {AUTH_HEADER_COPY.logoutLabel}
        </Button>
      )}
    </Space>
  )
}
