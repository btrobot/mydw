import { Alert, Button, Card, Form, Input, Space, Typography, message } from 'antd'
import { useMutation } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
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
      message.error(descriptor.title)
    },
  })

  const statusAlert = useMemo(() => {
    const source = authStatusQuery.data ?? session
    if (!source || source.auth_state === 'unauthenticated' || source.auth_state === 'authenticated_active') {
      return null
    }
    const descriptor = getAuthStateDescriptor(source)
    return descriptor ? (
      <AuthErrorMessage descriptor={descriptor} testId="auth-login-status-message" />
    ) : null
  }, [authStatusQuery.data, session])

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
        title="登录本地工作台"
        style={{ width: 480, maxWidth: '100%' }}
        data-testid="auth-login-page"
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            登录后即可继续使用作品工作台、运行总览和任务诊断等本地能力。
          </Typography.Paragraph>

          {authStatusQuery.isLoading && session ? (
            <Alert
              type="info"
              showIcon
              message="正在同步授权状态"
              description="正在刷新当前设备的授权信息，请稍候。"
            />
          ) : null}

          {authStatusQuery.isError && session ? (
            <Alert
              type="warning"
              showIcon
              message="授权状态暂时无法刷新"
              description="登录页仍可继续提交，但当前设备状态尚未完成最新同步。"
              action={<Button size="small" onClick={() => void authStatusQuery.refetch()}>重试</Button>}
            />
          ) : null}

          {statusAlert}

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

          {submitError && (
            <AuthErrorMessage
              descriptor={submitError}
              onRetry={() => form.submit()}
              testId="auth-login-error-message"
            />
          )}

          <div data-testid="auth-login-device-meta">
            <Typography.Paragraph type="secondary" style={{ marginBottom: 4 }}>
              本机授权信息仅用于当前设备登录校验，不影响页面主流程。
            </Typography.Paragraph>
            <Typography.Text type="secondary">设备标识：{deviceId}</Typography.Text>
            <br />
            <Typography.Text type="secondary">客户端版本：{clientVersion}</Typography.Text>
          </div>
        </Space>
      </Card>
    </div>
  )
}
