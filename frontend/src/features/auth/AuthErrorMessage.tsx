import { Alert, Button, Typography } from 'antd'

import type { AuthErrorDescriptor } from './authErrorHandler'

interface AuthErrorMessageProps {
  descriptor: AuthErrorDescriptor
  onRetry?: () => void
  retryLabel?: string
  testId?: string
  label?: string
}

export default function AuthErrorMessage({
  descriptor,
  onRetry,
  retryLabel,
  testId = 'auth-error-message',
  label,
}: AuthErrorMessageProps) {
  if (label && !onRetry) {
    return (
      <div
        data-testid={testId}
        style={{
          border: '1px solid #f0f0f0',
          borderRadius: 8,
          padding: 12,
          background: '#fafafa',
        }}
      >
        <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
          {label}
        </Typography.Text>
        <Typography.Text strong style={{ display: 'block', marginBottom: 4 }}>
          {descriptor.title}
        </Typography.Text>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {descriptor.description}
        </Typography.Paragraph>
      </div>
    )
  }

  return (
    <div data-testid={testId}>
      {label ? (
        <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
          {label}
        </Typography.Text>
      ) : null}
      <Alert
        type={descriptor.severity}
        showIcon
        message={descriptor.title}
        description={
          <Typography.Paragraph style={{ marginBottom: 0 }}>
            {descriptor.description}
          </Typography.Paragraph>
        }
        action={
          onRetry ? (
            <Button size="small" onClick={onRetry}>
              {retryLabel ?? descriptor.retryLabel ?? '重试'}
            </Button>
          ) : undefined
        }
      />
    </div>
  )
}
