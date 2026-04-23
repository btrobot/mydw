import { Alert, Button, Card, Flex, Space, Statistic, Typography } from 'antd'

import type { WorkbenchSummaryCounts } from './shared'

const { Paragraph, Text } = Typography

type WorkbenchSummaryCardProps = {
  creativeFlowLabel: string
  showDiagnosticsNotice: boolean
  summary: WorkbenchSummaryCounts
  onOpenDiagnostics: () => void
}

export default function WorkbenchSummaryCard({
  creativeFlowLabel,
  showDiagnosticsNotice,
  summary,
  onOpenDiagnostics,
}: WorkbenchSummaryCardProps) {
  return (
    <Card data-testid="creative-workbench-publish-summary">
      <Flex justify="space-between" align="start" gap={16} wrap="wrap">
        <Space direction="vertical" size={4}>
          <Text type="secondary" data-testid="creative-workbench-main-entry-banner">
            入口模式：{creativeFlowLabel}
          </Text>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            默认先处理作品 brief、素材编排、审核与 AIClip；运行侧信息请从“查看运行诊断”进入。
          </Paragraph>
        </Space>
        <Button onClick={onOpenDiagnostics} data-testid="creative-workbench-open-diagnostics">
          查看运行诊断
        </Button>
      </Flex>

      {showDiagnosticsNotice && (
        <Alert
          type="warning"
          showIcon
          message="部分运行诊断暂不可用，可通过“查看运行诊断”重试。"
          description="当前不影响作品主流程，可稍后进入诊断抽屉重试。"
          style={{ marginTop: 16 }}
          data-testid="creative-workbench-diagnostics-notice"
        />
      )}

      <Flex wrap gap={24}>
        <Statistic title="作品数" value={summary.all_count} />
        <Statistic title="待审核" value={summary.waiting_review_count} />
        <Statistic title="待补充" value={summary.pending_input_count} />
        <Statistic title="已进发布池" value={summary.active_pool_count} />
        <Statistic title="池版本已对齐" value={summary.aligned_pool_count} />
      </Flex>
    </Card>
  )
}
