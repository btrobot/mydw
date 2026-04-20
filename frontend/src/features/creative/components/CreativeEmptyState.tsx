import { Button, Empty, Space, Typography } from 'antd'

import type { CreativeFlowMode } from '../creativeFlow'
import { creativeFlowModeMeta } from '../creativeFlow'

const { Paragraph, Text } = Typography

interface CreativeEmptyStateProps {
  mode?: CreativeFlowMode
  onCreateCreative?: () => void
  onOpenLegacyTaskEntry?: () => void
}

export default function CreativeEmptyState({
  mode = 'creative_first',
  onCreateCreative,
  onOpenLegacyTaskEntry,
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
        </Space>
      )}
    >
      <Space wrap>
        {onCreateCreative ? (
          <Button type="primary" onClick={onCreateCreative}>
            新建作品
          </Button>
        ) : null}
        {onOpenLegacyTaskEntry ? (
          <Button onClick={onOpenLegacyTaskEntry}>
            兼容入口：新建任务
          </Button>
        ) : null}
      </Space>
    </Empty>
  )
}
