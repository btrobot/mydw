import { Flex, Spin, Typography } from 'antd'
import type { ReactNode } from 'react'

interface PageLoadingProps {
  title?: ReactNode
  description?: ReactNode
  fullHeight?: boolean
  testId?: string
}

export function PageLoading({ title, description, fullHeight = false, testId }: PageLoadingProps) {
  return (
    <Flex
      vertical
      align="center"
      justify="center"
      gap={12}
      style={{ minHeight: fullHeight ? '100vh' : 160, padding: 24 }}
      data-testid={testId}
    >
      <Spin />
      {title ? <Typography.Text strong>{title}</Typography.Text> : null}
      {description ? <Typography.Text type="secondary">{description}</Typography.Text> : null}
    </Flex>
  )
}
