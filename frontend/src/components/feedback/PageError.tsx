import { Alert } from 'antd'
import type { ReactNode } from 'react'

interface PageErrorProps {
  title: ReactNode
  description?: ReactNode
  extra?: ReactNode
  testId?: string
  type?: 'error' | 'warning'
}

export function PageError({
  title,
  description,
  extra,
  testId,
  type = 'warning',
}: PageErrorProps) {
  return (
    <Alert
      type={type}
      showIcon
      message={title}
      description={description}
      action={extra}
      data-testid={testId}
    />
  )
}
