import { ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Descriptions, Drawer, Space, Tag, Typography } from 'antd'

import DiagnosticsActionPanel, { type DiagnosticsRecommendation } from '../diagnostics/DiagnosticsActionPanel'

type WorkbenchDiagnosticsDrawerProps = {
  actionRecommendations: DiagnosticsRecommendation[]
  creativeFlowDescription: string
  creativeFlowLabel: string
  creativeFlowShadowCompare: boolean
  effectiveSchedulerModeLabel: string
  hasDiagnosticsError: boolean
  killSwitchLabel: string
  onClose: () => void
  onRetryAuxiliary: () => void
  open: boolean
  runtimeStatusLabel: string
  schedulerModeLabel: string
  shadowReadLabel: string
  activePoolCount: number
  alignedPoolCount: number
}

const { Paragraph } = Typography

export default function WorkbenchDiagnosticsDrawer({
  actionRecommendations,
  creativeFlowDescription,
  creativeFlowLabel,
  creativeFlowShadowCompare,
  effectiveSchedulerModeLabel,
  hasDiagnosticsError,
  killSwitchLabel,
  onClose,
  onRetryAuxiliary,
  open,
  runtimeStatusLabel,
  schedulerModeLabel,
  shadowReadLabel,
  activePoolCount,
  alignedPoolCount,
}: WorkbenchDiagnosticsDrawerProps) {
  return (
    <Drawer
      title="运行诊断"
      open={open}
      onClose={onClose}
      destroyOnClose
      width={520}
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }} data-testid="creative-workbench-diagnostics-drawer">
        {hasDiagnosticsError && (
          <Alert
            type="warning"
            showIcon
            message="发布运行诊断暂时不可用"
            description="发布状态或调度配置加载失败，当前不能把失败伪装成空闲状态。"
            action={(
              <Button size="small" icon={<ReloadOutlined />} onClick={onRetryAuxiliary}>
                重试
              </Button>
            )}
            data-testid="creative-workbench-runtime-warning"
          />
        )}

        <DiagnosticsActionPanel
          title="推荐行动"
          recommendations={actionRecommendations}
          testId="creative-workbench-diagnostics-actions"
        />

        <Card size="small" title="运行态摘要">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="入口模式">
              <Space wrap>
                <Tag data-testid="creative-workbench-main-entry-diagnostics">{creativeFlowLabel}</Tag>
                <Tag data-testid="creative-workbench-shadow-compare">
                  Shadow Compare：{creativeFlowShadowCompare ? '开启' : '关闭'}
                </Tag>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="配置模式">
              <Tag data-testid="creative-workbench-scheduler-mode">{schedulerModeLabel}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="生效模式">
              <Tag data-testid="creative-workbench-effective-mode">{effectiveSchedulerModeLabel}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="运行状态">
              <Tag data-testid="creative-workbench-runtime-status">{runtimeStatusLabel}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Shadow Read">
              <Tag data-testid="creative-workbench-shadow-read">{shadowReadLabel}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Kill Switch">
              <Tag data-testid="creative-workbench-kill-switch">{killSwitchLabel}</Tag>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Card size="small" title="发布池诊断">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="已进发布池">
              {activePoolCount}
            </Descriptions.Item>
            <Descriptions.Item label="池版本已对齐">
              {alignedPoolCount}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {creativeFlowDescription} 这里仅保留运行排障与发布池观察信息。
        </Paragraph>
      </Space>
    </Drawer>
  )
}
