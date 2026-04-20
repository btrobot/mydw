import { Card, Spin, Typography } from 'antd'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react'

import { AUTH_SESSION_QUERY_KEY, fetchAuthSession } from './api'
import AuthErrorMessage from './AuthErrorMessage'
import { AUTH_BOOTSTRAP_COPY, getBootstrapErrorDescriptor } from './authErrorHandler'
import { installAuthTransportSync } from './transport'
import type { AuthBootstrapStatus, AuthState, LocalAuthSessionSummary } from './types'

interface AuthContextValue {
  session: LocalAuthSessionSummary | null
  authState: AuthState | 'unknown'
  bootstrapStatus: AuthBootstrapStatus
  bootstrapError: string | null
  refreshSession: () => Promise<LocalAuthSessionSummary | null>
  setSession: (session: LocalAuthSessionSummary | null) => void
}

const BOOTSTRAP_ERROR_FALLBACK = 'Session restore failed.'
const USE_AUTH_ERROR = 'useAuth must be used within AuthBootstrapProvider.'

const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

const AuthBootstrapScreen = () => (
  <div
    data-testid="auth-bootstrap-loading"
    style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f0f2f5',
      padding: 24,
    }}
  >
    <Card style={{ width: 480, maxWidth: '100%' }}>
      <Spin size="large" tip={AUTH_BOOTSTRAP_COPY.loadingTip}>
        <div data-testid="auth-bootstrap-loading-copy" style={{ minHeight: 72 }}>
          <Typography.Title level={4} style={{ marginTop: 0, marginBottom: 8 }}>
            {AUTH_BOOTSTRAP_COPY.loadingTitle}
          </Typography.Title>
          <Typography.Text type="secondary">
            {AUTH_BOOTSTRAP_COPY.loadingDescription}
          </Typography.Text>
        </div>
      </Spin>
    </Card>
  </div>
)

export const AuthBootstrapProvider = ({ children }: AuthProviderProps) => {
  const queryClient = useQueryClient()

  const authSessionQuery = useQuery({
    queryKey: AUTH_SESSION_QUERY_KEY,
    queryFn: fetchAuthSession,
    retry: 0,
    staleTime: 0,
    refetchOnWindowFocus: false,
  })

  const session = authSessionQuery.data ?? null
  const bootstrapStatus: AuthBootstrapStatus = authSessionQuery.isPending
    ? 'loading'
    : authSessionQuery.isError
      ? 'error'
      : 'ready'

  const bootstrapError = authSessionQuery.isError
    ? authSessionQuery.error instanceof Error
      ? authSessionQuery.error.message
      : BOOTSTRAP_ERROR_FALLBACK
    : null

  const authState: AuthState | 'unknown' = session?.auth_state ?? (bootstrapStatus === 'error' ? 'unknown' : 'unauthenticated')

  const setSession = useCallback(
    (nextSession: LocalAuthSessionSummary | null) => {
      queryClient.setQueryData(AUTH_SESSION_QUERY_KEY, nextSession)
    },
    [queryClient]
  )

  const refreshSession = useCallback(async () => {
    const result = await authSessionQuery.refetch()
    return result.data ?? null
  }, [authSessionQuery])

  useEffect(() => {
    const uninstall = installAuthTransportSync(queryClient, setSession)
    return () => uninstall()
  }, [queryClient, setSession])

  useEffect(() => {
    document.documentElement.dataset.authBootstrapStatus = bootstrapStatus
    document.documentElement.dataset.authState = authState
    document.documentElement.dataset.authBootstrapError = bootstrapError ? 'true' : 'false'

    return () => {
      delete document.documentElement.dataset.authBootstrapStatus
      delete document.documentElement.dataset.authState
      delete document.documentElement.dataset.authBootstrapError
    }
  }, [authState, bootstrapError, bootstrapStatus])

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      authState,
      bootstrapStatus,
      bootstrapError,
      refreshSession,
      setSession,
    }),
    [session, authState, bootstrapStatus, bootstrapError, refreshSession, setSession]
  )

  return (
    <AuthContext.Provider value={value}>
      {bootstrapStatus === 'loading' ? (
        <AuthBootstrapScreen />
      ) : (
        <>
          {bootstrapStatus === 'error' && (
            <div style={{ padding: 16 }}>
              <AuthErrorMessage
                descriptor={getBootstrapErrorDescriptor(
                  authSessionQuery.error ?? new Error(bootstrapError ?? BOOTSTRAP_ERROR_FALLBACK)
                )}
                onRetry={() => void refreshSession()}
                retryLabel={authSessionQuery.isFetching ? AUTH_BOOTSTRAP_COPY.retryingLabel : AUTH_BOOTSTRAP_COPY.retryLabel}
                testId="auth-bootstrap-error"
              />
            </div>
          )}
          {children}
        </>
      )}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error(USE_AUTH_ERROR)
  }
  return context
}
