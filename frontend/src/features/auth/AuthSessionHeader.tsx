import { Button, Space, Tag, Typography, message } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { logoutAuth } from './api'
import { useAuth } from './AuthProvider'

const { Text } = Typography

const STATUS_META: Record<
  string,
  {
    color: string
    label: string
  }
> = {
  authenticated_active: { color: 'success', label: '已授权' },
  authenticated_grace: { color: 'warning', label: '宽限模式' },
  revoked: { color: 'error', label: '已失效' },
  device_mismatch: { color: 'error', label: '设备不匹配' },
  expired: { color: 'warning', label: '已过期' },
  unauthenticated: { color: 'default', label: '未登录' },
  error: { color: 'warning', label: '异常' },
}

export default function AuthSessionHeader() {
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
    () => STATUS_META[authState] ?? { color: 'default', label: authState },
    [authState]
  )

  return (
    <Space data-testid="auth-session-header">
      {session?.display_name && <Text style={{ color: 'white' }}>{session.display_name}</Text>}
      <Tag color={meta.color}>{meta.label}</Tag>
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
