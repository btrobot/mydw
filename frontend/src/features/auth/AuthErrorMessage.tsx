import { Alert, Button, Typography } from 'antd'

import type { AuthErrorDescriptor } from './authErrorHandler'

interface AuthErrorMessageProps {
  descriptor: AuthErrorDescriptor
  onRetry?: () => void
  retryLabel?: string
  testId?: string
}

export default function AuthErrorMessage({
  descriptor,
  onRetry,
  retryLabel,
  testId = 'auth-error-message',
}: AuthErrorMessageProps) {
  return (
    <div data-testid={testId}>
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
