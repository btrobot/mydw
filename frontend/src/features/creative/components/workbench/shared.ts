import type {
  CreativeWorkbenchItem,
  CreativeWorkbenchPoolState,
} from '../../types/creative'
import { creativeStatusMeta } from '../../types/creative'

export type WorkbenchSortKind = 'updated_desc' | 'updated_asc' | 'attention_desc' | 'failed_desc'
export type WorkbenchPresetKey = 'all' | 'waiting_review' | 'needs_rework' | 'recent_failures' | 'version_mismatch'
export type WorkbenchDiagnosticsView = 'runtime'

export type WorkbenchQueryState = {
  keyword?: string
  status?: keyof typeof creativeStatusMeta
  poolState?: CreativeWorkbenchPoolState
  preset?: WorkbenchPresetKey
  sort: WorkbenchSortKind
  page: number
  pageSize: number
}

export type WorkbenchRouteState = {
  queryState: WorkbenchQueryState
  diagnostics?: WorkbenchDiagnosticsView
}

export type WorkbenchTableRow = CreativeWorkbenchItem & {
  poolState: CreativeWorkbenchPoolState
  poolAligned: boolean
  hasRecentFailure: boolean
  attentionScore: number
}

export type WorkbenchFormValues = {
  keyword?: string | null
  status?: keyof typeof creativeStatusMeta | null
  poolState?: CreativeWorkbenchPoolState | null
  preset?: WorkbenchPresetKey
  current?: number
  pageSize?: number
}

export type WorkbenchSummaryCounts = {
  all_count: number
  waiting_review_count: number
  pending_input_count: number
  needs_rework_count: number
  recent_failures_count: number
  active_pool_count: number
  aligned_pool_count: number
  version_mismatch_count: number
}

export const defaultWorkbenchSummary: WorkbenchSummaryCounts = {
  all_count: 0,
  waiting_review_count: 0,
  pending_input_count: 0,
  needs_rework_count: 0,
  recent_failures_count: 0,
  active_pool_count: 0,
  aligned_pool_count: 0,
  version_mismatch_count: 0,
}
