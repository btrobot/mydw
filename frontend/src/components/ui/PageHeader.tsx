import { Flex, Space, Typography } from 'antd'
import type { CSSProperties, ReactNode } from 'react'

const { Paragraph, Title } = Typography

interface PageHeaderProps {
  title: ReactNode
  subtitle?: ReactNode
  extra?: ReactNode
  testId?: string
  style?: CSSProperties
}

export function PageHeader({ title, subtitle, extra, testId, style }: PageHeaderProps) {
  return (
    <Flex
      justify="space-between"
      align="flex-start"
      gap={16}
      wrap="wrap"
      style={style}
      data-testid={testId}
    >
      <Space direction="vertical" size={4} style={{ flex: '1 1 320px', minWidth: 0 }}>
        <Title level={3} style={{ margin: 0 }}>
          {title}
        </Title>
        {subtitle ? (
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {subtitle}
          </Paragraph>
        ) : null}
      </Space>
      {extra ? (
        <div style={{ flex: '0 0 auto', maxWidth: '100%' }}>
          {extra}
        </div>
      ) : null}
    </Flex>
  )
}
