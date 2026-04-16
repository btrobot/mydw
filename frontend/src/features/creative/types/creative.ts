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
}

export const formatCreativeTimestamp = (value: string): string =>
  new Date(value).toLocaleString('zh-CN')
