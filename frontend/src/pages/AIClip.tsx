import { PageContainer } from '@ant-design/pro-components'
import { Alert, Typography } from 'antd'

import AIClipWorkflowPanel from '@/features/creative/components/AIClipWorkflowPanel'

const { Paragraph } = Typography

export default function AIClip() {
  return (
    <PageContainer
      title="AIClip 独立工作流"
      subTitle="适合单独试跑处理链路，也保持与作品内工作流一致"
      data-testid="ai-clip-tool-page"
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="这个入口用于独立试跑 AIClip"
        description="如果你要把处理结果直接提交为新的创意版本，建议从作品详情页打开 AIClip 工作流。"
      />
      <Paragraph type="secondary">
        这里仍然复用同一块 AIClip workflow panel，但更强调“选择素材 → 配置 → 执行 → 预览”的完整处理顺序。
      </Paragraph>

      <AIClipWorkflowPanel />
    </PageContainer>
  )
}
