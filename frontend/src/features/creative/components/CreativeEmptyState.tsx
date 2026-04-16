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
          <Text strong>暂无作品</Text>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            阶段 A 仅接入 Creative 骨架。当前还没有映射到作品域的任务样本时，这里会显示空态。
          </Paragraph>
        </Space>
      )}
    >
      {onOpenTaskList ? (
        <Button type="primary" onClick={onOpenTaskList}>
          前往任务列表
        </Button>
      ) : null}
    </Empty>
  )
}
