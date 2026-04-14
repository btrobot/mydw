import { Alert, Card, Space, Typography, message } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import AuthErrorMessage from '../AuthErrorMessage'
import { AUTH_ADMIN_SESSIONS_QUERY_KEY, AUTH_SESSION_QUERY_KEY, fetchAdminSessions, revokeAdminSession } from '../api'
import { useAuth } from '../AuthProvider'
import { getAuthErrorDescriptor } from '../authErrorHandler'
import SessionList from './SessionList'

export default function SessionAdmin() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { setSession } = useAuth()

  const sessionsQuery = useQuery({
    queryKey: AUTH_ADMIN_SESSIONS_QUERY_KEY,
    queryFn: fetchAdminSessions,
    retry: 0,
    staleTime: 0,
    refetchOnWindowFocus: false,
  })

  const revokeMutation = useMutation({
    mutationFn: revokeAdminSession,
    onSuccess: (payload) => {
      queryClient.setQueryData(AUTH_ADMIN_SESSIONS_QUERY_KEY, (current: typeof sessionsQuery.data) =>
        (current ?? []).map((item) =>
          item.session_id === payload.revoked_session.session_id ? payload.revoked_session : item
        )
      )
      queryClient.setQueryData(AUTH_SESSION_QUERY_KEY, payload.current_session)
      setSession(payload.current_session)
      message.success('Session revoked')
      if (payload.revoked_session.is_current_session) {
        navigate('/auth/revoked', { replace: true })
      }
    },
    onError: (error: unknown) => {
      const descriptor = getAuthErrorDescriptor(error)
      message.error(descriptor.title)
    },
  })

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title="Auth session admin" data-testid="auth-admin-page">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            Review persisted local authorization sessions and revoke the current machine session when you need to force a re-login.
          </Typography.Paragraph>
          <Alert
            type="warning"
            showIcon
            message="Revoking a session signs out the current machine session"
            description="This action clears local auth tokens and redirects the shell to the revoked authorization screen."
          />

          {sessionsQuery.isError ? (
            <AuthErrorMessage
              descriptor={getAuthErrorDescriptor(sessionsQuery.error)}
              onRetry={() => void sessionsQuery.refetch()}
              testId="auth-admin-error"
            />
          ) : (
            <SessionList
              sessions={sessionsQuery.data ?? []}
              onRevoke={(session) => revokeMutation.mutate(session.session_id)}
              revokingSessionId={revokeMutation.variables ?? null}
            />
          )}
        </Space>
      </Card>
    </Space>
  )
}
