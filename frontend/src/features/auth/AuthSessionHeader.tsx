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
  authenticated_active: { color: 'success', label: 'Authenticated' },
  authenticated_grace: { color: 'warning', label: 'Grace' },
  revoked: { color: 'error', label: 'Revoked' },
  device_mismatch: { color: 'error', label: 'Device mismatch' },
  expired: { color: 'warning', label: 'Expired' },
  unauthenticated: { color: 'default', label: 'Unauthenticated' },
  error: { color: 'warning', label: 'Error' },
}

export default function AuthSessionHeader() {
  const { session, authState, setSession } = useAuth()
  const navigate = useNavigate()

  const logoutMutation = useMutation({
    mutationFn: logoutAuth,
    onSuccess: (nextSession) => {
      setSession(nextSession)
      message.success('Signed out')
      navigate('/login', { replace: true })
    },
    onError: (error: unknown) => {
      if (error instanceof Error) {
        message.error(error.message)
        return
      }
      message.error('Failed to sign out')
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
          Sign out
        </Button>
      )}
    </Space>
  )
}
