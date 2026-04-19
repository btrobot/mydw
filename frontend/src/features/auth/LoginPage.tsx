import { App as AntApp, Button, Card, Collapse, Form, Input, Space, Typography } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import AuthErrorMessage from './AuthErrorMessage'
import { useAuth } from './AuthProvider'
import { getAuthErrorDescriptor, getAuthStateDescriptor, type AuthErrorDescriptor } from './authErrorHandler'
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
  const { message } = AntApp.useApp()
  const { session, setSession } = useAuth()
  const [deviceId, setDeviceId] = useState(() => getOrCreateDeviceId())
  const [clientVersion, setClientVersion] = useState('web-dev')
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
      message.success('登录成功')
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
              登录应用
            </Typography.Title>
            <Typography.Text type="secondary">
              登录后即可继续使用作品工作台、任务管理和素材管理。
            </Typography.Text>
          </Space>
        )}
        style={{ width: 480, maxWidth: '100%' }}
        data-testid="auth-login-page"
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            当前登录会绑定到本设备，用于保护你的应用访问权限。
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
              label="用户名"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input placeholder="请输入用户名" />
            </Form.Item>
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password placeholder="请输入密码" />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loginMutation.isPending}
                style={{ width: '100%' }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          {submitError ? (
            <AuthErrorMessage
              descriptor={submitError}
              onRetry={() => form.submit()}
              retryLabel="重新提交"
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
                    ? '正在同步当前登录状态，请稍候。'
                    : '状态同步暂时不可用，你仍可继续提交登录。'}
                </Typography.Text>
                {statusSyncMode === 'error' ? (
                  <Button type="link" size="small" onClick={() => void authStatusQuery.refetch()}>
                    重试同步
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
                label: <span data-testid="auth-login-diagnostics-trigger">设备与版本信息</span>,
                children: (
                  <div data-testid="auth-login-device-meta">
                    <Typography.Paragraph type="secondary" style={{ marginBottom: 4 }}>
                      以下信息仅用于支持排查当前设备的登录环境，不影响页面主流程。
                    </Typography.Paragraph>
                    <Typography.Text type="secondary">设备标识：{deviceId}</Typography.Text>
                    <br />
                    <Typography.Text type="secondary">客户端版本：{clientVersion}</Typography.Text>
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
