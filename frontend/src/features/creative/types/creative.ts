import type {
  CreativeCurrentVersionResponse,
  CreativeDetailResponse,
  CreativeStatus,
  CreativeWorkbenchItemResponse,
} from '@/api'

export type CreativeWorkbenchItem = CreativeWorkbenchItemResponse
export type CreativeDetail = CreativeDetailResponse
export type CreativeCurrentVersion = CreativeCurrentVersionResponse

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

export const formatCreativeTimestamp = (value: string): string =>
  new Date(value).toLocaleString('zh-CN')
