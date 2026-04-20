import { Button, Card, Checkbox, Collapse, Form, Input, Space, Typography } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import AuthErrorMessage from './AuthErrorMessage'
import { useAuth } from './AuthProvider'
import {
  AUTH_LOGIN_COPY,
  getAuthErrorDescriptor,
  getAuthStateDescriptor,
  type AuthErrorDescriptor,
} from './authErrorHandler'
import { loginAuth } from './api'
import { getClientVersion, getOrCreateDeviceId, setStoredDeviceId } from './device'
import { useAuthStatus } from './useAuthStatus'

interface LoginFormValues {
  username: string
  password: string
}

export default function LoginPage() {
  const [form] = Form.useForm<LoginFormValues>()
  const navigate = useNavigate()
  const { session, setSession } = useAuth()
  const [deviceId, setDeviceId] = useState(() => getOrCreateDeviceId())
  const [clientVersion, setClientVersion] = useState('web-dev')
  const [rememberChoice, setRememberChoice] = useState(false)
  const [submitError, setSubmitError] = useState<AuthErrorDescriptor | null>(null)
  const authStatusQuery = useAuthStatus(Boolean(session))

  useEffect(() => {
    let mounted = true
    void getClientVersion().then((version) => {
      if (mounted) {
        setClientVersion(version)
      }
    })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const persistedDeviceId = authStatusQuery.data?.device_id ?? session?.device_id
    if (!persistedDeviceId || persistedDeviceId === deviceId) {
      return
    }
    setStoredDeviceId(persistedDeviceId)
    setDeviceId(persistedDeviceId)
  }, [authStatusQuery.data?.device_id, deviceId, session?.device_id])

  const loginMutation = useMutation({
    mutationFn: async (values: LoginFormValues) =>
      loginAuth({
        username: values.username,
        password: values.password,
        device_id: deviceId,
        client_version: clientVersion,
      }),
    onSuccess: (nextSession) => {
      setSubmitError(null)
      setSession(nextSession)
      navigate('/creative/workbench', { replace: true })
    },
    onError: (error: unknown) => {
      const descriptor = getAuthErrorDescriptor(error)
      setSubmitError(descriptor)
    },
  })

  const loginStateSource = authStatusQuery.data ?? session
  let loginStateDescriptor: AuthErrorDescriptor | null = null
  if (
    loginStateSource
    && (loginStateSource.auth_state === 'refresh_required' || loginStateSource.auth_state === 'error')
  ) {
    loginStateDescriptor = getAuthStateDescriptor(loginStateSource)
  }
  const statusSyncMode = session && !submitError && !loginStateDescriptor
    ? authStatusQuery.isLoading
      ? 'loading'
      : authStatusQuery.isError
        ? 'error'
        : null
    : null

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
        title={(
          <Space direction="vertical" size={2}>
            <Typography.Title level={4} style={{ margin: 0 }}>
              {AUTH_LOGIN_COPY.title}
            </Typography.Title>
            <Typography.Text type="secondary">
              {AUTH_LOGIN_COPY.subtitle}
            </Typography.Text>
          </Space>
        )}
        style={{ width: 480, maxWidth: '100%' }}
        data-testid="auth-login-page"
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {AUTH_LOGIN_COPY.helper}
          </Typography.Paragraph>

          <Form
            form={form}
            layout="vertical"
            onValuesChange={() => {
              if (submitError) {
                setSubmitError(null)
              }
            }}
            onFinish={(values) => loginMutation.mutate(values)}
            autoComplete="off"
          >
            <Form.Item
              name="username"
              label={AUTH_LOGIN_COPY.usernameLabel}
              rules={[{ required: true, message: AUTH_LOGIN_COPY.usernameRequiredMessage }]}
            >
              <Input placeholder={AUTH_LOGIN_COPY.usernamePlaceholder} autoFocus />
            </Form.Item>
            <Form.Item
              name="password"
              label={AUTH_LOGIN_COPY.passwordLabel}
              rules={[{ required: true, message: AUTH_LOGIN_COPY.passwordRequiredMessage }]}
            >
              <Input.Password placeholder={AUTH_LOGIN_COPY.passwordPlaceholder} />
            </Form.Item>

            <Space direction="vertical" size={4} style={{ width: '100%', marginBottom: 24 }}>
              <Checkbox
                checked={rememberChoice}
                onChange={(event) => setRememberChoice(event.target.checked)}
                data-testid="auth-login-remember-me"
              >
                {AUTH_LOGIN_COPY.rememberMeLabel}
              </Checkbox>
              <Typography.Text
                type="secondary"
                data-testid="auth-login-remember-me-hint"
              >
                {AUTH_LOGIN_COPY.rememberMeHint}
              </Typography.Text>
            </Space>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loginMutation.isPending}
                style={{ width: '100%' }}
              >
                {AUTH_LOGIN_COPY.submitLabel}
              </Button>
            </Form.Item>
          </Form>

          {submitError ? (
            <AuthErrorMessage
              descriptor={submitError}
              onRetry={() => form.submit()}
              retryLabel={AUTH_LOGIN_COPY.retryLabel}
              testId="auth-login-error-message"
            />
          ) : loginStateDescriptor ? (
            <AuthErrorMessage descriptor={loginStateDescriptor} testId="auth-login-status-message" />
          ) : null}

          {statusSyncMode ? (
            <div data-testid="auth-login-status-sync">
              <Space size={8} wrap>
                <Typography.Text type="secondary">
                  {statusSyncMode === 'loading'
                    ? AUTH_LOGIN_COPY.statusSyncLoading
                    : AUTH_LOGIN_COPY.statusSyncError}
                </Typography.Text>
                {statusSyncMode === 'error' ? (
                  <Button type="link" size="small" onClick={() => void authStatusQuery.refetch()}>
                    {AUTH_LOGIN_COPY.statusSyncRetryLabel}
                  </Button>
                ) : null}
              </Space>
            </div>
          ) : null}

          <Collapse
            bordered={false}
            size="small"
            items={[
              {
                key: 'diagnostics',
                label: <span data-testid="auth-login-diagnostics-trigger">{AUTH_LOGIN_COPY.diagnosticsLabel}</span>,
                children: (
                  <div data-testid="auth-login-device-meta">
                    <Typography.Paragraph type="secondary" style={{ marginBottom: 4 }}>
                      {AUTH_LOGIN_COPY.diagnosticsDescription}
                    </Typography.Paragraph>
                    <Typography.Text type="secondary">
                      {AUTH_LOGIN_COPY.diagnosticsDeviceIdLabel}：{deviceId}
                    </Typography.Text>
                    <br />
                    <Typography.Text type="secondary">
                      {AUTH_LOGIN_COPY.diagnosticsClientVersionLabel}：{clientVersion}
                    </Typography.Text>
                  </div>
                ),
              },
            ]}
          />
        </Space>
      </Card>
    </div>
  )
}
