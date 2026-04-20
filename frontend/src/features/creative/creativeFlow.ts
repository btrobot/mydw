import type { SystemConfigResponse } from '@/api'

export type CreativeFlowMode = NonNullable<SystemConfigResponse['creative_flow_mode']>

export const DEFAULT_CREATIVE_FLOW_MODE: CreativeFlowMode = 'creative_first'
export const DEFAULT_CREATIVE_FLOW_SHADOW_COMPARE = false

export const creativeFlowModeMeta: Record<
  CreativeFlowMode,
  {
    label: string
    description: string
    defaultPath: string
    legacyEntryProminence: 'primary' | 'secondary'
  }
> = {
  task_first: {
    label: '任务优先',
    description: '默认落到兼容任务创建入口；作品工作台作为可回退的新入口保留。',
    defaultPath: '/task/create',
    legacyEntryProminence: 'primary',
  },
  dual: {
    label: '双轨过渡',
    description: '默认落到作品工作台，同时保留兼容任务创建入口用于对照与回退。',
    defaultPath: '/creative/workbench',
    legacyEntryProminence: 'secondary',
  },
  creative_first: {
    label: '作品优先',
    description: '默认落到作品工作台；任务创建仅作为兼容/高级入口保留。',
    defaultPath: '/creative/workbench',
    legacyEntryProminence: 'secondary',
  },
}

export const resolveCreativeFlowMode = (
  config?: Pick<SystemConfigResponse, 'creative_flow_mode'> | null,
): CreativeFlowMode => config?.creative_flow_mode ?? DEFAULT_CREATIVE_FLOW_MODE

export const resolveCreativeFlowShadowCompare = (
  config?: Pick<SystemConfigResponse, 'creative_flow_shadow_compare'> | null,
): boolean => config?.creative_flow_shadow_compare ?? DEFAULT_CREATIVE_FLOW_SHADOW_COMPARE

export const getCreativeFlowDefaultPath = (
  config?: Pick<SystemConfigResponse, 'creative_flow_mode'> | null,
): string => creativeFlowModeMeta[resolveCreativeFlowMode(config)].defaultPath
