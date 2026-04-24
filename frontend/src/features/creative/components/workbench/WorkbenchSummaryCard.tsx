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
        <div data-testid="creative-workbench-summary-all-count">
          <Statistic title="作品数" value={summary.all_count} />
        </div>
        <div data-testid="creative-workbench-summary-waiting-review-count">
          <Statistic title="待审核" value={summary.waiting_review_count} />
        </div>
        <div data-testid="creative-workbench-summary-pending-input-count">
          <Statistic title="待补充" value={summary.pending_input_count} />
        </div>
        <div data-testid="creative-workbench-summary-active-pool-count">
          <Statistic title="已进发布池" value={summary.active_pool_count} />
        </div>
        <div data-testid="creative-workbench-summary-aligned-pool-count">
          <Statistic title="池版本已对齐" value={summary.aligned_pool_count} />
        </div>
        <div data-testid="creative-workbench-summary-selected-video-count">
          <Statistic title="入选视频" value={summary.selected_video_count} />
        </div>
        <div data-testid="creative-workbench-summary-selected-audio-count">
          <Statistic title="入选音频" value={summary.selected_audio_count} />
        </div>
        <div data-testid="creative-workbench-summary-candidate-video-count">
          <Statistic title="候选视频" value={summary.candidate_video_count} />
        </div>
        <div data-testid="creative-workbench-summary-candidate-audio-count">
          <Statistic title="候选音频" value={summary.candidate_audio_count} />
        </div>
        <div data-testid="creative-workbench-summary-candidate-cover-count">
          <Statistic title="候选封面" value={summary.candidate_cover_count} />
        </div>
        <div data-testid="creative-workbench-summary-definition-ready-count">
          <Statistic title="定义就绪" value={summary.definition_ready_count} />
        </div>
        <div data-testid="creative-workbench-summary-composition-ready-count">
          <Statistic title="可提交合成" value={summary.composition_ready_count} />
        </div>
      </Flex>
    </Card>
  )
}
