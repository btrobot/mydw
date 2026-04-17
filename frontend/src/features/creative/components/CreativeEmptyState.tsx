import { Button, Empty, Space, Typography } from 'antd'

const { Paragraph, Text } = Typography

interface CreativeEmptyStateProps {
  onOpenTaskList?: () => void
}

export default function CreativeEmptyState({ onOpenTaskList }: CreativeEmptyStateProps) {
  return (
    <Empty
      description={(
        <Space direction="vertical" size={4}>
          <Text strong>No creatives yet</Text>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            Creative workbench becomes most useful after tasks have written back into the creative domain. Until then, this page stays empty and you can inspect execution progress from task diagnostics.
          </Paragraph>
        </Space>
      )}
    >
      {onOpenTaskList ? (
        <Button type="primary" onClick={onOpenTaskList}>
          Open task diagnostics
        </Button>
      ) : null}
    </Empty>
  )
}
