import { Alert } from 'antd'
import type { ReactNode } from 'react'

interface InlineNoticeProps {
  message: ReactNode
  description?: ReactNode
  action?: ReactNode
  type?: 'success' | 'info' | 'warning' | 'error'
  testId?: string
}

export function InlineNotice({
  message,
  description,
  action,
  type = 'info',
  testId,
}: InlineNoticeProps) {
  return (
    <Alert
      type={type}
      showIcon
      message={message}
      description={description}
      action={action}
      data-testid={testId}
    />
  )
}
