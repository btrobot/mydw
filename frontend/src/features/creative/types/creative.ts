import type {
  CheckRecordResponse,
  CreativeCurrentVersionResponse,
  CreativeDetailResponse,
  CreativeReviewConclusion,
  CreativeReviewSummaryResponse,
  CreativeStatus,
  CreativeVersionSummaryResponse,
  CreativeWorkbenchItemResponse,
} from '@/api'

export type CreativeWorkbenchItem = CreativeWorkbenchItemResponse
export type CreativeDetail = CreativeDetailResponse
export type CreativeCurrentVersion = CreativeCurrentVersionResponse
export type CreativeVersionSummary = CreativeVersionSummaryResponse
export type CreativeReviewSummary = CreativeReviewSummaryResponse
export type CreativeCheckRecord = CheckRecordResponse

export const creativeStatusMeta: Record<CreativeStatus, { color: string; label: string }> = {
  PENDING_INPUT: {
    color: 'default',
    label: '待补充',
  },
  WAITING_REVIEW: {
    color: 'processing',
    label: '待审核',
  },
  APPROVED: {
    color: 'success',
    label: '已通过',
  },
  REWORK_REQUIRED: {
    color: 'warning',
    label: '待返工',
  },
  REJECTED: {
    color: 'error',
    label: '已驳回',
  },
}

export const creativeReviewConclusionMeta: Record<
  CreativeReviewConclusion,
  { color: string; label: string; tone: 'success' | 'warning' | 'error' }
> = {
  APPROVED: {
    color: 'success',
    label: '通过',
    tone: 'success',
  },
  REWORK_REQUIRED: {
    color: 'warning',
    label: '返工',
    tone: 'warning',
  },
  REJECTED: {
    color: 'error',
    label: '驳回',
    tone: 'error',
  },
}

export const formatCreativeTimestamp = (value?: string | null): string => {
  if (!value) {
    return '-'
  }

  return new Date(value).toLocaleString('zh-CN')
}

export const getVersionLabel = (versionNo?: number | null): string =>
  versionNo ? `V${versionNo}` : '未命名版本'

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

export const formatCheckConclusion = (check: CreativeCheckRecord | null | undefined): string => {
  if (!check) {
    return '暂无审核记录'
  }

  const meta = creativeReviewConclusionMeta[check.conclusion]
  return check.rework_type ? `${meta.label} · ${check.rework_type}` : meta.label
}
