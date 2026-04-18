import { PageContainer } from '@ant-design/pro-components'
import { Alert, Typography } from 'antd'

import AIClipWorkflowPanel from '@/features/creative/components/AIClipWorkflowPanel'

const { Paragraph } = Typography

export default function AIClip() {
  return (
    <PageContainer
      title="AIClip \u72ec\u7acb\u5de5\u4f5c\u6d41"
      subTitle="\u9002\u5408\u5355\u72ec\u8bd5\u8dd1\u5904\u7406\u94fe\u8def\uff0c\u4e5f\u4fdd\u6301\u4e0e\u4f5c\u54c1\u5185\u5de5\u4f5c\u6d41\u4e00\u81f4"
      data-testid="ai-clip-tool-page"
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="\u8fd9\u4e2a\u5165\u53e3\u7528\u4e8e\u72ec\u7acb\u8bd5\u8dd1 AIClip"
        description="\u5982\u679c\u4f60\u8981\u628a\u5904\u7406\u7ed3\u679c\u76f4\u63a5\u63d0\u4ea4\u4e3a\u65b0\u7684\u521b\u610f\u7248\u672c\uff0c\u5efa\u8bae\u4ece\u4f5c\u54c1\u8be6\u60c5\u9875\u6253\u5f00 AIClip \u5de5\u4f5c\u6d41\u3002"
      />
      <Paragraph type="secondary">
        \u8fd9\u91cc\u4ecd\u7136\u590d\u7528\u540c\u4e00\u5757 AIClip workflow panel\uff0c\u4f46\u66f4\u5f3a\u8c03\u201c\u9009\u62e9\u7d20\u6750 \u2192 \u914d\u7f6e \u2192 \u6267\u884c \u2192 \u9884\u89c8\u201d\u7684\u5b8c\u6574\u5904\u7406\u987a\u5e8f\u3002
      </Paragraph>

      <AIClipWorkflowPanel />
    </PageContainer>
  )
}
