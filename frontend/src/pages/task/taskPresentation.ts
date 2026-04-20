import type { TaskKind, TaskStatus } from '@/api'

export const taskStatusMeta: Record<TaskStatus, { color: string; text: string }> = {
  draft: { color: 'default', text: '待合成' },
  composing: { color: 'processing', text: '合成中' },
  ready: { color: 'warning', text: '待上传' },
  uploading: { color: 'processing', text: '上传中' },
  uploaded: { color: 'success', text: '已上传' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
}

export const taskKindMeta: Record<TaskKind, { color: string; text: string }> = {
  composition: { color: 'purple', text: '合成任务' },
  publish: { color: 'blue', text: '发布任务' },
}

export const terminalTaskStates: ReadonlySet<TaskStatus> = new Set<TaskStatus>([
  'uploaded',
  'cancelled',
])

export type TaskPrimaryActionKey =
  | 'detail'
  | 'submitComposition'
  | 'publish'
  | 'retry'

export function getTaskActionAvailability(status: TaskStatus) {
  const canSubmitComposition = status === 'draft'
  const canCancelComposition = status === 'composing'
  const canPublish = status === 'ready'
  const canRetry = status === 'failed'
  const canEditRetry = status === 'failed'
  const canCancel = !terminalTaskStates.has(status) && status !== 'failed'

  return {
    canSubmitComposition,
    canCancelComposition,
    canPublish,
    canRetry,
    canEditRetry,
    canCancel,
    canDelete: true,
  }
}

export function getTaskPrimaryAction(status: TaskStatus): TaskPrimaryActionKey {
  if (status === 'draft') return 'submitComposition'
  if (status === 'ready') return 'publish'
  if (status === 'failed') return 'retry'
  return 'detail'
}
