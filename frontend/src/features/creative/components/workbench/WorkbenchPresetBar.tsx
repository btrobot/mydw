import { Button, Space, Typography } from 'antd'

import type { WorkbenchPresetKey } from './shared'

const { Text } = Typography

const workbenchPresetMeta: Record<WorkbenchPresetKey, { label: string }> = {
  all: { label: '全部' },
  waiting_review: { label: '待审核' },
  needs_rework: { label: '需返工' },
  recent_failures: { label: '最近失败' },
  version_mismatch: { label: '版本未对齐' },
}

type WorkbenchPresetBarProps = {
  appliedPreset?: WorkbenchPresetKey
  counts: Record<WorkbenchPresetKey, number>
  onPresetChange: (preset: WorkbenchPresetKey) => void
}

export default function WorkbenchPresetBar({
  appliedPreset,
  counts,
  onPresetChange,
}: WorkbenchPresetBarProps) {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size={12}>
      <Space wrap>
        <Text type="secondary">高频视角：</Text>
        {(Object.keys(workbenchPresetMeta) as WorkbenchPresetKey[]).map((preset) => (
          <Button
            key={preset}
            size="small"
            type={appliedPreset === preset || (!appliedPreset && preset === 'all') ? 'primary' : 'default'}
            onClick={() => onPresetChange(preset)}
            data-testid={`creative-workbench-preset-${preset}`}
          >
            {workbenchPresetMeta[preset].label}（{counts[preset]}）
          </Button>
        ))}
      </Space>
    </Space>
  )
}
