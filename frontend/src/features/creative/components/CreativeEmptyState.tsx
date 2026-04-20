import { Button, Empty, Space, Typography } from 'antd'

import type { CreativeFlowMode } from '../creativeFlow'
import { creativeFlowModeMeta } from '../creativeFlow'

const { Paragraph, Text } = Typography

interface CreativeEmptyStateProps {
  mode?: CreativeFlowMode
  onCreateCreative?: () => void
}

export default function CreativeEmptyState({
  mode = 'creative_first',
  onCreateCreative,
}: CreativeEmptyStateProps) {
  const modeMeta = creativeFlowModeMeta[mode]

  return (
    <Empty
      description={(
        <Space direction="vertical" size={4}>
          <Text strong>还没有作品</Text>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            先创建一条作品，再逐步补齐素材、合成配置与执行动作。当前入口模式：{modeMeta.label}。
          </Paragraph>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {modeMeta.description}
          </Paragraph>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            执行记录、失败重试与排障仍在任务管理中查看；日常创作请从作品开始。
          </Paragraph>
        </Space>
      )}
    >
      <Space wrap>
        {onCreateCreative ? (
          <Button type="primary" onClick={onCreateCreative}>
            新建作品
          </Button>
        ) : null}
      </Space>
    </Empty>
  )
}
