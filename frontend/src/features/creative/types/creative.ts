import type {
  CheckRecordResponse,
  CreativeCurrentVersionResponse,
  CreativeDetailResponse,
  CreativeReviewConclusion,
  CreativeReviewSummaryResponse,
  CreativeStatus,
  CreativeVersionSummaryResponse,
  CreativeWorkbenchItemResponse,
  PublishPoolItemResponse,
  PublishPoolStatus,
  PublishSchedulerMode,
  PublishStatus,
  PublishStatusResponse,
  ScheduleConfigResponse,
} from '@/api'

export type CreativeWorkbenchItem = CreativeWorkbenchItemResponse
export type CreativeDetail = CreativeDetailResponse
export type CreativeCurrentVersion = CreativeCurrentVersionResponse
export type CreativeVersionSummary = CreativeVersionSummaryResponse
export type CreativeReviewSummary = CreativeReviewSummaryResponse
export type CreativeCheckRecord = CheckRecordResponse
export type PublishPoolItem = PublishPoolItemResponse
export type PublishRuntimeStatus = PublishStatusResponse
export type PublishScheduleConfig = ScheduleConfigResponse
export type CreativeWorkbenchPoolState = 'in_pool' | 'out_pool' | 'version_mismatch'

export const creativeStatusMeta: Record<CreativeStatus, { color: string; label: string }> = {
  PENDING_INPUT: { color: 'default', label: '待补输入' },
  READY_TO_COMPOSE: { color: 'processing', label: '待提交合成' },
  COMPOSING: { color: 'processing', label: '合成中' },
  WAITING_REVIEW: { color: 'processing', label: '待审核' },
  APPROVED: { color: 'success', label: '已通过' },
  REWORK_REQUIRED: { color: 'warning', label: '需返工' },
  REJECTED: { color: 'error', label: '已驳回' },
  IN_PUBLISH_POOL: { color: 'processing', label: '待发布' },
  PUBLISHING: { color: 'processing', label: '发布中' },
  PUBLISHED: { color: 'success', label: '已发布' },
  FAILED: { color: 'error', label: '已失败' },
}

export const creativeReviewConclusionMeta: Record<
  CreativeReviewConclusion,
  { color: string; label: string; tone: 'success' | 'warning' | 'error' }
> = {
  APPROVED: { color: 'success', label: '通过', tone: 'success' },
  REWORK_REQUIRED: { color: 'warning', label: '返工', tone: 'warning' },
  REJECTED: { color: 'error', label: '驳回', tone: 'error' },
}

export const REWORK_TYPE_LABELS: Record<string, string> = {
  COPY_REWORK: '文案返工',
  ASSET_REWORK: '素材返工',
  SHOT_REWORK: '镜头返工',
  STRUCTURE_REWORK: '结构返工',
}

export const publishPoolStatusMeta: Record<PublishPoolStatus, { color: string; label: string }> = {
  active: { color: 'success', label: '池中生效' },
  invalidated: { color: 'default', label: '已失效' },
}

export const publishSchedulerModeMeta: Record<PublishSchedulerMode, { color: string; label: string }> = {
  task: { color: 'default', label: 'Task 模式' },
  pool: { color: 'processing', label: 'Pool 模式' },
}

export const publishRuntimeStatusMeta: Record<PublishStatus, { color: string; label: string }> = {
  idle: { color: 'default', label: '空闲' },
  running: { color: 'processing', label: '运行中' },
  paused: { color: 'warning', label: '已暂停' },
}

export const creativeWorkbenchPoolStateMeta: Record<CreativeWorkbenchPoolState, { color: string; label: string }> = {
  in_pool: { color: 'success', label: '已入发布池' },
  out_pool: { color: 'default', label: '未入发布池' },
  version_mismatch: { color: 'warning', label: '版本未对齐' },
}

export const formatCreativeTimestamp = (value?: string | null): string => {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleString('zh-CN')
}

export const getVersionLabel = (versionNo?: number | null): string =>
  versionNo ? `V${versionNo}` : '未标版本'

export const getVersionTitle = (
  version: Pick<CreativeVersionSummary, 'title' | 'version_no'>,
): string => version.title?.trim() || `${getVersionLabel(version.version_no)} 版本`

export const isCurrentEffectiveCheck = (
  reviewSummary: CreativeReviewSummary | null | undefined,
  check: CreativeCheckRecord | null | undefined,
): boolean =>
  Boolean(
    reviewSummary?.current_version_id !== undefined
      && reviewSummary?.current_version_id !== null
      && check
      && reviewSummary.current_check?.id === check.id,
  )

export const formatReworkTypeLabel = (value?: string | null): string => {
  if (!value) {
    return '-'
  }
  return REWORK_TYPE_LABELS[value] ?? value
}

export const formatCheckConclusion = (check: CreativeCheckRecord | null | undefined): string => {
  if (!check) {
    return '暂无审核结论'
  }
  const meta = creativeReviewConclusionMeta[check.conclusion]
  return check.rework_type ? `${meta.label} / ${formatReworkTypeLabel(check.rework_type)}` : meta.label
}

export const isPoolVersionAligned = (
  poolItem: Pick<PublishPoolItem, 'creative_version_id' | 'creative_current_version_id'>,
): boolean => poolItem.creative_version_id === poolItem.creative_current_version_id

export const getCreativeWorkbenchPoolState = (
  poolItem: Pick<PublishPoolItem, 'creative_version_id' | 'creative_current_version_id'> | null | undefined,
): CreativeWorkbenchPoolState => {
  if (!poolItem) {
    return 'out_pool'
  }
  return isPoolVersionAligned(poolItem) ? 'in_pool' : 'version_mismatch'
}

export const formatModeLabel = (mode?: PublishSchedulerMode | null): string =>
  mode ? publishSchedulerModeMeta[mode].label : '-'

export const formatRuntimeStatusLabel = (status?: PublishStatus | null): string =>
  status ? publishRuntimeStatusMeta[status].label : '-'

export const formatShadowDiffReasons = (value: unknown): string[] => {
  if (!value || typeof value !== 'object') {
    return []
  }
  const reasons = (value as { reasons?: unknown }).reasons
  return Array.isArray(reasons) ? reasons.filter((item): item is string => typeof item === 'string') : []
}

export const getShadowDiffFlag = (value: unknown): boolean => {
  if (!value || typeof value !== 'object') {
    return false
  }
  return Boolean((value as { differs?: unknown }).differs)
}

export const formatShadowDiffJson = (value: unknown): string => {
  if (!value) {
    return '{}'
  }
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return '{}'
  }
}
