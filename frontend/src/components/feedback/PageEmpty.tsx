import { Empty, Space, Typography } from 'antd'
import type { ReactNode } from 'react'

interface PageEmptyProps {
  title: ReactNode
  description?: ReactNode
  extra?: ReactNode
  testId?: string
}

export function PageEmpty({ title, description, extra, testId }: PageEmptyProps) {
  return (
    <div style={{ padding: 24 }} data-testid={testId}>
      <Space direction="vertical" size={12} style={{ width: '100%', alignItems: 'center' }}>
        <Empty description={false} />
        <Typography.Text strong>{title}</Typography.Text>
        {description ? <Typography.Text type="secondary">{description}</Typography.Text> : null}
        {extra}
      </Space>
    </div>
  )
}
