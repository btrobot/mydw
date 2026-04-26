import { Alert, Button, Card, Form, Input, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';

import { AdminApiError, mapLoginError } from '../../features/auth/auth-client.js';
import { useAuth } from '../../features/auth/auth-context.js';

type LoginFormValues = {
  username: string;
  password: string;
};

export function LoginPage(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const { status, login, authNotice, clearAuthNotice } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    document.title = 'Remote Admin';
  }, []);

  if (status === 'authenticated') {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f5f7fa',
        padding: 24,
      }}
    >
      <Card style={{ width: 420, maxWidth: '100%' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Typography.Title level={3} style={{ marginBottom: 8 }}>
              Remote Admin
            </Typography.Title>
            <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
              Sign in to the protected admin control plane on top of the existing remote authorization backend.
            </Typography.Paragraph>
          </div>

          {authNotice ? (
            <Alert type="info" showIcon message={authNotice} closable onClose={clearAuthNotice} />
          ) : null}
          {errorMessage ? <Alert type="error" showIcon message={errorMessage} /> : null}

          <Form<LoginFormValues>
            layout="vertical"
            initialValues={{ username: '', password: '' }}
            onFinish={async (values) => {
              setSubmitting(true);
              setErrorMessage(null);
              try {
                await login(values.username.trim(), values.password);
                const redirectTarget =
                  typeof location.state === 'object' &&
                  location.state !== null &&
                  'from' in location.state &&
                  typeof (location.state as { from?: unknown }).from === 'string'
                    ? ((location.state as { from: string }).from || '/dashboard')
                    : '/dashboard';
                navigate(redirectTarget, { replace: true });
              } catch (error) {
                setErrorMessage(
                  error instanceof AdminApiError ? mapLoginError(error.errorCode) : mapLoginError()
                );
              } finally {
                setSubmitting(false);
              }
            }}
          >
            <Form.Item label="Username" name="username" rules={[{ required: true, message: 'Please enter the admin username.' }]}>
              <Input autoComplete="username" placeholder="admin" />
            </Form.Item>
            <Form.Item label="Password" name="password" rules={[{ required: true, message: 'Please enter the password.' }]}>
              <Input.Password autoComplete="current-password" placeholder="Enter your password" />
            </Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              Sign in
            </Button>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
