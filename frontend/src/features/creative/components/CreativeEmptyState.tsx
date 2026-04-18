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
          <Text strong>还没有可处理的作品</Text>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            当执行结果还没有回写到作品域时，这里会暂时为空。你可以先到“任务诊断”查看执行进度，等作品生成后再回到工作台继续处理。
          </Paragraph>
        </Space>
      )}
    >
      {onOpenTaskList ? (
        <Button type="primary" onClick={onOpenTaskList}>
          打开任务诊断
        </Button>
      ) : null}
    </Empty>
  )
}
