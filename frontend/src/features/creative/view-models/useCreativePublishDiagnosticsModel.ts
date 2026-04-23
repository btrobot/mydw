import { useCallback, useMemo } from 'react'

import { creativeFlowModeMeta, resolveCreativeFlowMode, resolveCreativeFlowShadowCompare } from '../creativeFlow'
import {
  usePublishPoolItems,
  usePublishStatus,
  useScheduleConfig,
} from '../hooks/useCreatives'
import {
  formatModeLabel,
  formatRuntimeStatusLabel,
  formatShadowDiffReasons,
  getShadowDiffFlag,
  isPoolVersionAligned,
  type CreativeDetail,
  type CreativeVersionSummary,
  type PublishPackageRecord,
} from '../types/creative'
import { useSystemConfig } from '@/hooks/useSystem'

type UseCreativePublishDiagnosticsModelParams = {
  creativeId: number | undefined
  creative: CreativeDetail | undefined
  prioritizedTaskId: number | undefined
  versionById: Map<number, CreativeVersionSummary>
  currentPackageRecord: PublishPackageRecord | null
}

export function useCreativePublishDiagnosticsModel({
  creativeId,
  creative,
  prioritizedTaskId,
  versionById,
  currentPackageRecord,
}: UseCreativePublishDiagnosticsModelParams) {
  const publishStatusQuery = usePublishStatus()
  const scheduleConfigQuery = useScheduleConfig()
  const systemConfigQuery = useSystemConfig()
  const activePoolQuery = usePublishPoolItems({
    creativeId,
    status: 'active',
    limit: 50,
    enabled: creativeId !== undefined,
  })
  const invalidatedPoolQuery = usePublishPoolItems({
    creativeId,
    status: 'invalidated',
    limit: 50,
    enabled: creativeId !== undefined,
  })

  const publishStatus = publishStatusQuery.data
  const scheduleConfig = scheduleConfigQuery.data
  const systemConfig = systemConfigQuery.data
  const creativeFlowMode = resolveCreativeFlowMode(systemConfig)
  const creativeFlowShadowCompare = resolveCreativeFlowShadowCompare(systemConfig)
  const creativeFlowMeta = creativeFlowModeMeta[creativeFlowMode]

  const activePoolItems = activePoolQuery.data?.items ?? []
  const invalidatedPoolItems = useMemo(
    () => [...(invalidatedPoolQuery.data?.items ?? [])].sort((left, right) => right.updated_at.localeCompare(left.updated_at)),
    [invalidatedPoolQuery.data?.items],
  )

  const currentPoolItem = useMemo(() => {
    if (!creative?.current_version_id) {
      return activePoolItems[0] ?? null
    }

    return (
      activePoolItems.find((item) => item.creative_version_id === creative.current_version_id)
      ?? activePoolItems[0]
      ?? null
    )
  }, [activePoolItems, creative?.current_version_id])

  const latestInvalidatedPoolItem = invalidatedPoolItems[0] ?? null
  const currentPoolVersion = currentPoolItem ? versionById.get(currentPoolItem.creative_version_id) ?? null : null
  const currentPoolPackageRecord = currentPoolVersion?.package_record ?? currentPackageRecord
  const latestInvalidatedPoolVersion = latestInvalidatedPoolItem
    ? versionById.get(latestInvalidatedPoolItem.creative_version_id) ?? null
    : null
  const publishPoolRecords = useMemo(
    () => [...activePoolItems, ...invalidatedPoolItems].map((item) => ({
      item,
      aligned: isPoolVersionAligned(item),
      packageRecord: versionById.get(item.creative_version_id)?.package_record ?? null,
    })),
    [activePoolItems, invalidatedPoolItems, versionById],
  )

  const diagnosticTaskIds = useMemo(() => {
    const ids = new Set<number>()
    if (prioritizedTaskId) {
      ids.add(prioritizedTaskId)
    }
    for (const taskId of creative?.linked_task_ids ?? []) {
      ids.add(taskId)
    }
    if (publishStatus?.current_task_id) {
      ids.add(publishStatus.current_task_id)
    }
    return Array.from(ids)
  }, [creative?.linked_task_ids, prioritizedTaskId, publishStatus?.current_task_id])

  const primaryTaskId = diagnosticTaskIds[0]
  const schedulerMode = publishStatus?.scheduler_mode ?? scheduleConfig?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatus?.effective_scheduler_mode ?? schedulerMode
  const shadowDiff = publishStatus?.scheduler_shadow_diff
  const currentPublishTaskId = publishStatus?.current_task_id ?? null
  const shadowDiffReasons = formatShadowDiffReasons(shadowDiff)
  const shadowDiffDiffers = getShadowDiffFlag(shadowDiff)
  const diagnosticsUnavailable =
    publishStatusQuery.isError
    || scheduleConfigQuery.isError
    || activePoolQuery.isError
    || invalidatedPoolQuery.isError

  const refetchDiagnostics = useCallback(() => Promise.all([
    publishStatusQuery.refetch(),
    scheduleConfigQuery.refetch(),
    systemConfigQuery.refetch(),
    activePoolQuery.refetch(),
    invalidatedPoolQuery.refetch(),
  ]), [activePoolQuery, invalidatedPoolQuery, publishStatusQuery, scheduleConfigQuery, systemConfigQuery])

  const retryDiagnostics = useCallback(() => {
    void refetchDiagnostics()
  }, [refetchDiagnostics])

  const schedulerModeLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : formatModeLabel(schedulerMode)
  const effectiveSchedulerModeLabel = publishStatusQuery.isError
    ? '获取失败'
    : formatModeLabel(effectiveSchedulerMode)
  const runtimeStatusLabel = publishStatusQuery.isError
    ? '获取失败'
    : formatRuntimeStatusLabel(publishStatus?.status)
  const shadowReadLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : (publishStatus?.publish_pool_shadow_read ?? scheduleConfig?.publish_pool_shadow_read)
        ? '开启'
        : '关闭'
  const killSwitchLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : (publishStatus?.publish_pool_kill_switch ?? scheduleConfig?.publish_pool_kill_switch)
        ? '开启'
        : '关闭'

  return {
    publishStatusQuery,
    scheduleConfigQuery,
    activePoolQuery,
    invalidatedPoolQuery,
    publishStatus,
    scheduleConfig,
    creativeFlowMeta,
    creativeFlowShadowCompare,
    activePoolItems,
    invalidatedPoolItems,
    currentPoolItem,
    latestInvalidatedPoolItem,
    currentPoolPackageRecord,
    latestInvalidatedPoolVersion,
    publishPoolRecords,
    diagnosticTaskIds,
    primaryTaskId,
    schedulerMode,
    effectiveSchedulerMode,
    shadowDiff,
    currentPublishTaskId,
    shadowDiffReasons,
    shadowDiffDiffers,
    diagnosticsUnavailable,
    refetchDiagnostics,
    retryDiagnostics,
    schedulerModeLabel,
    effectiveSchedulerModeLabel,
    runtimeStatusLabel,
    shadowReadLabel,
    killSwitchLabel,
  }
}
