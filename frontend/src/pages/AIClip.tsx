import { PageContainer } from '@ant-design/pro-components'
import { Typography } from 'antd'

import AIClipWorkflowPanel from '@/features/creative/components/AIClipWorkflowPanel'

const { Paragraph } = Typography

export default function AIClip() {
  return (
    <PageContainer
      title="AI 剪辑"
      subTitle="独立工具页 wrapper"
      data-testid="ai-clip-tool-page"
    >
      <Paragraph type="secondary">
        该页面继续保留为独立工具页；Creative 内部复用的是同一套 AIClip panel / hook 边界，而不是整页路由硬嵌。
      </Paragraph>

      <AIClipWorkflowPanel />
    </PageContainer>
  )
}
