import { App as AntApp, Button, Space, Tag, Typography } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { logoutAuth } from './api'
import { useAuth } from './AuthProvider'
import type { AuthState } from './types'

const { Text } = Typography

const STATUS_META: Record<
  AuthState,
  {
    color: string
    label: string
  }
> = {
  authenticated_active: { color: 'success', label: '已登录' },
  authenticated_grace: { color: 'warning', label: '宽限模式' },
  revoked: { color: 'error', label: '权限失效' },
  device_mismatch: { color: 'error', label: '设备未校验' },
  expired: { color: 'warning', label: '登录过期' },
  refresh_required: { color: 'warning', label: '待重新确认' },
  authorizing: { color: 'processing', label: '校验中' },
  unauthenticated: { color: 'default', label: '未登录' },
  error: { color: 'warning', label: '状态异常' },
}

const UNKNOWN_STATUS_META = { color: 'default', label: '状态未知' } as const

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
    () => (authState === 'unknown' ? UNKNOWN_STATUS_META : STATUS_META[authState]),
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
          退出登录
        </Button>
      )}
    </Space>
  )
}
