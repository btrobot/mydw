import { ReloadOutlined } from '@ant-design/icons'
import { PageContainer } from '@ant-design/pro-components'
import type { ProFormInstance } from '@ant-design/pro-components'
import { useCallback, useEffect, useMemo, useRef } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import {
  App,
  Button,
  Card,
  Flex,
  Result,
  Space,
  Spin,
} from 'antd'

import CreativeEmptyState from '../components/CreativeEmptyState'
import WorkbenchDiagnosticsDrawer from '../components/workbench/WorkbenchDiagnosticsDrawer'
import WorkbenchPresetBar from '../components/workbench/WorkbenchPresetBar'
import WorkbenchSummaryCard from '../components/workbench/WorkbenchSummaryCard'
import type {
  WorkbenchDiagnosticsView,
  WorkbenchFormValues,
  WorkbenchPresetKey,
  WorkbenchQueryState,
  WorkbenchRouteState,
  WorkbenchSortKind,
  WorkbenchTableRow,
} from '../components/workbench/shared'
import { defaultWorkbenchSummary } from '../components/workbench/shared'
import WorkbenchTable from '../components/workbench/WorkbenchTable'
import {
  creativeFlowModeMeta,
  resolveCreativeFlowMode,
  resolveCreativeFlowShadowCompare,
} from '../creativeFlow'
import {
  useCreatives,
  useCreateCreative,
  usePublishStatus,
  useScheduleConfig,
} from '../hooks/useCreatives'
import { useSystemConfig } from '@/hooks/useSystem'
import type {
  CreativeWorkbenchItem,
  CreativeWorkbenchPoolState,
} from '../types/creative'
import {
  creativeStatusMeta,
  creativeWorkbenchPoolStateMeta,
  formatModeLabel,
  formatRuntimeStatusLabel,
} from '../types/creative'

const DEFAULT_WORKBENCH_PAGE_SIZE = 10
const workbenchPresetKeys: WorkbenchPresetKey[] = [
  'all',
  'waiting_review',
  'needs_rework',
  'recent_failures',
  'version_mismatch',
]

const getAttentionScore = (item: CreativeWorkbenchItem, poolState: CreativeWorkbenchPoolState): number => {
  let score = 0

  if (item.generation_error_msg || item.status === 'FAILED' || item.generation_failed_at) {
    score += 400
  }

  if (item.status === 'REWORK_REQUIRED') {
    score += 300
  }

  if (item.status === 'WAITING_REVIEW') {
    score += 200
  }

  if (poolState === 'version_mismatch') {
    score += 100
  }

  return score
}

const parsePositiveInteger = (value: string | null, fallback: number): number => {
  if (!value) {
    return fallback
  }

  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

const parseWorkbenchSortKind = (value: string | null): WorkbenchSortKind => {
  switch (value) {
    case 'updated_asc':
    case 'updated_at:ascend':
      return 'updated_asc'
    case 'attention_desc':
      return 'attention_desc'
    case 'failed_desc':
      return 'failed_desc'
    case 'updated_desc':
    case 'updated_at:descend':
    default:
      return 'updated_desc'
  }
}

const parseWorkbenchPreset = (value: string | null): WorkbenchPresetKey | undefined =>
  value && workbenchPresetKeys.includes(value as WorkbenchPresetKey) ? value as WorkbenchPresetKey : undefined

const parseWorkbenchDiagnosticsView = (value: string | null): WorkbenchDiagnosticsView | undefined =>
  value === 'runtime' ? value : undefined

const isPresetCompatible = (
  preset: WorkbenchPresetKey | undefined,
  values: Pick<WorkbenchFormValues, 'keyword' | 'status' | 'poolState'>,
  sort: WorkbenchSortKind,
): boolean => {
  if (!preset) {
    return false
  }

  const keyword = values.keyword?.trim()

  switch (preset) {
    case 'all':
      return !keyword && !values.status && !values.poolState && sort === 'updated_desc'
    case 'waiting_review':
      return !keyword && values.status === 'WAITING_REVIEW' && !values.poolState && sort === 'updated_desc'
    case 'needs_rework':
      return !keyword && values.status === 'REWORK_REQUIRED' && !values.poolState && sort === 'updated_desc'
    case 'recent_failures':
      return !keyword && !values.status && !values.poolState && sort === 'failed_desc'
    case 'version_mismatch':
      return !keyword && !values.status && values.poolState === 'version_mismatch' && sort === 'attention_desc'
    default:
      return false
  }
}

const getPresetState = (
  preset: WorkbenchPresetKey,
  pageSize: number,
): WorkbenchQueryState => {
  switch (preset) {
    case 'waiting_review':
      return { preset, status: 'WAITING_REVIEW', sort: 'updated_desc', page: 1, pageSize }
    case 'needs_rework':
      return { preset, status: 'REWORK_REQUIRED', sort: 'updated_desc', page: 1, pageSize }
    case 'recent_failures':
      return { preset, sort: 'failed_desc', page: 1, pageSize }
    case 'version_mismatch':
      return { preset, poolState: 'version_mismatch', sort: 'attention_desc', page: 1, pageSize }
    case 'all':
    default:
      return { preset: 'all', sort: 'updated_desc', page: 1, pageSize }
  }
}

const parseWorkbenchStateFromSearchParams = (searchParams: URLSearchParams): WorkbenchRouteState => {
  const keyword = searchParams.get('keyword')?.trim() || undefined
  const statusValue = searchParams.get('status')
  const poolStateValue = searchParams.get('poolState')
  const preset = parseWorkbenchPreset(searchParams.get('preset'))
  const diagnostics = parseWorkbenchDiagnosticsView(searchParams.get('diagnostics'))

  const status = statusValue && statusValue in creativeStatusMeta
    ? statusValue as keyof typeof creativeStatusMeta
    : undefined
  const poolState = poolStateValue && poolStateValue in creativeWorkbenchPoolStateMeta
    ? poolStateValue as CreativeWorkbenchPoolState
    : undefined

  return {
    queryState: {
      keyword,
      status,
      poolState,
      preset,
      sort: parseWorkbenchSortKind(searchParams.get('sort')),
      page: parsePositiveInteger(searchParams.get('page'), 1),
      pageSize: parsePositiveInteger(searchParams.get('pageSize'), DEFAULT_WORKBENCH_PAGE_SIZE),
    },
    diagnostics,
  }
}

const buildWorkbenchSearchParams = (
  queryState: WorkbenchQueryState,
  diagnostics?: WorkbenchDiagnosticsView,
): URLSearchParams => {
  const nextSearchParams = new URLSearchParams()
  const keyword = queryState.keyword?.trim()

  if (keyword) {
    nextSearchParams.set('keyword', keyword)
  }

  if (queryState.status) {
    nextSearchParams.set('status', queryState.status)
  }

  if (queryState.poolState) {
    nextSearchParams.set('poolState', queryState.poolState)
  }

  const preset = isPresetCompatible(queryState.preset, queryState, queryState.sort) ? queryState.preset : undefined

  if (preset) {
    nextSearchParams.set('preset', preset)
  }

  nextSearchParams.set('sort', queryState.sort)
  nextSearchParams.set('page', String(queryState.page))
  nextSearchParams.set('pageSize', String(queryState.pageSize))

  if (diagnostics) {
    nextSearchParams.set('diagnostics', diagnostics)
  }

  return nextSearchParams
}

const getWorkbenchFormValues = (queryState: WorkbenchQueryState): WorkbenchFormValues => ({
  keyword: queryState.keyword ?? '',
  status: queryState.status ?? null,
  poolState: queryState.poolState ?? null,
  preset: queryState.preset,
})

const getAppliedWorkbenchFilters = (
  values: Pick<WorkbenchFormValues, 'keyword' | 'status' | 'poolState' | 'preset'>,
): Pick<WorkbenchQueryState, 'keyword' | 'status' | 'poolState' | 'preset'> => ({
  keyword: values.keyword?.trim() || undefined,
  status: values.status ?? undefined,
  poolState: values.poolState ?? undefined,
  preset: values.preset,
})

export default function CreativeWorkbench() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { message } = App.useApp()
  const formRef = useRef<ProFormInstance<WorkbenchFormValues>>()
  const routeState = useMemo(
    () => parseWorkbenchStateFromSearchParams(searchParams),
    [searchParams],
  )
  const appliedQueryState = routeState.queryState
  const appliedFormValues = useMemo(
    () => getWorkbenchFormValues(appliedQueryState),
    [
      appliedQueryState.keyword,
      appliedQueryState.status,
      appliedQueryState.poolState,
      appliedQueryState.preset,
    ],
  )
  const creativesQuery = useCreatives({
    skip: (appliedQueryState.page - 1) * appliedQueryState.pageSize,
    limit: appliedQueryState.pageSize,
    keyword: appliedQueryState.keyword,
    status: appliedQueryState.status,
    poolState: appliedQueryState.poolState,
    sort: appliedQueryState.sort,
    recentFailuresOnly: appliedQueryState.preset === 'recent_failures',
  })
  const createCreative = useCreateCreative()
  const publishStatusQuery = usePublishStatus()
  const scheduleConfigQuery = useScheduleConfig()
  const systemConfigQuery = useSystemConfig()

  const items = creativesQuery.data?.items ?? []
  const total = creativesQuery.data?.total ?? 0
  const summary = useMemo(
    () => ({
      ...defaultWorkbenchSummary,
      ...(creativesQuery.data?.summary ?? {}),
    }),
    [creativesQuery.data?.summary],
  )
  const diagnosticsOpen = routeState.diagnostics === 'runtime'

  const schedulerMode = publishStatusQuery.data?.scheduler_mode ?? scheduleConfigQuery.data?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatusQuery.data?.effective_scheduler_mode ?? schedulerMode
  const creativeFlowMode = resolveCreativeFlowMode(systemConfigQuery.data)
  const creativeFlowShadowCompare = resolveCreativeFlowShadowCompare(systemConfigQuery.data)
  const creativeFlowMeta = creativeFlowModeMeta[creativeFlowMode]

  const rows = useMemo<WorkbenchTableRow[]>(
    () => items.map((item) => {
      const poolState: CreativeWorkbenchPoolState = item.pool_state ?? 'out_pool'
      const hasRecentFailure = Boolean(item.generation_error_msg || item.status === 'FAILED' || item.generation_failed_at)
      return {
        ...item,
        poolState,
        poolAligned: item.active_pool_aligned ?? false,
        hasRecentFailure,
        attentionScore: getAttentionScore(item, poolState),
      }
    }),
    [items],
  )
  const workbenchPresetCounts = useMemo(
    () => ({
      all: summary.all_count,
      waiting_review: summary.waiting_review_count,
      needs_rework: summary.needs_rework_count,
      recent_failures: summary.recent_failures_count,
      version_mismatch: summary.version_mismatch_count,
    }),
    [summary],
  )

  useEffect(() => {
    formRef.current?.setFieldsValue(appliedFormValues)
  }, [appliedFormValues])

  const handleRetryPrimary = useCallback(() => {
    void creativesQuery.refetch()
  }, [creativesQuery])

  const handleRetryAuxiliary = useCallback(() => {
    void Promise.all([
      publishStatusQuery.refetch(),
      scheduleConfigQuery.refetch(),
      systemConfigQuery.refetch(),
    ])
  }, [publishStatusQuery, scheduleConfigQuery, systemConfigQuery])

  const handleCreateCreative = useCallback(async () => {
    try {
      const created = await createCreative.mutateAsync({})
      message.success('已创建作品，请继续填写 brief 并编排素材')
      navigate(`/creative/${created.id}`)
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('创建作品失败')
      }
    }
  }, [createCreative, message, navigate])

  const workbenchReturnTo = useMemo(() => {
    const currentPath = `${location.pathname}${location.search}`
    return currentPath || '/creative/workbench'
  }, [location.pathname, location.search])

  const openCreativeDetail = useCallback((
    creativeId: number,
    options?: { tool?: 'ai-clip' },
  ) => {
    const nextSearchParams = new URLSearchParams({ returnTo: workbenchReturnTo })

    if (options?.tool) {
      nextSearchParams.set('tool', options.tool)
    }

    navigate(`/creative/${creativeId}?${nextSearchParams.toString()}`)
  }, [navigate, workbenchReturnTo])

  const replaceWorkbenchSearchParams = useCallback((nextSearchParams: URLSearchParams) => {
    if (nextSearchParams.toString() !== searchParams.toString()) {
      setSearchParams(nextSearchParams, { replace: true })
    }
  }, [searchParams, setSearchParams])

  const updateRouteState = useCallback((
    nextQueryState: WorkbenchQueryState,
    diagnostics = routeState.diagnostics,
  ) => {
    const nextSearchParams = buildWorkbenchSearchParams(nextQueryState, diagnostics)
    replaceWorkbenchSearchParams(nextSearchParams)
  }, [replaceWorkbenchSearchParams, routeState.diagnostics])

  const handlePresetChange = useCallback((preset: WorkbenchPresetKey) => {
    updateRouteState(getPresetState(preset, appliedQueryState.pageSize))
  }, [appliedQueryState.pageSize, updateRouteState])

  const handleSortChange = useCallback((sort: WorkbenchSortKind) => {
    updateRouteState({
      ...appliedQueryState,
      sort,
      page: 1,
    })
  }, [appliedQueryState, updateRouteState])

  const setDiagnosticsView = useCallback((diagnostics?: WorkbenchDiagnosticsView) => {
    const nextSearchParams = new URLSearchParams(searchParams)

    if (diagnostics) {
      nextSearchParams.set('diagnostics', diagnostics)
    } else {
      nextSearchParams.delete('diagnostics')
    }
    replaceWorkbenchSearchParams(nextSearchParams)
  }, [replaceWorkbenchSearchParams, searchParams])

  const handleOpenDiagnostics = useCallback(() => {
    setDiagnosticsView('runtime')
  }, [setDiagnosticsView])

  const handleCloseDiagnostics = useCallback(() => {
    setDiagnosticsView(undefined)
  }, [setDiagnosticsView])

  const handleApplyFilters = useCallback((values: WorkbenchFormValues) => {
    updateRouteState({
      ...getAppliedWorkbenchFilters({
        keyword: values.keyword,
        status: values.status,
        poolState: values.poolState,
        preset: appliedQueryState.preset,
      }),
      sort: appliedQueryState.sort,
      page: 1,
      pageSize: appliedQueryState.pageSize,
    })
  }, [appliedQueryState.pageSize, appliedQueryState.preset, appliedQueryState.sort, updateRouteState])

  const handleResetFilters = useCallback(() => {
    updateRouteState(getPresetState('all', appliedQueryState.pageSize))
  }, [appliedQueryState.pageSize, updateRouteState])

  const handlePaginationChange = useCallback((page: number, pageSize: number) => {
    updateRouteState({
      ...appliedQueryState,
      page,
      pageSize,
    })
  }, [appliedQueryState, updateRouteState])

  const schedulerModeLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : formatModeLabel(schedulerMode)
  const effectiveSchedulerModeLabel = publishStatusQuery.isError
    ? '获取失败'
    : formatModeLabel(effectiveSchedulerMode)
  const runtimeStatusLabel = publishStatusQuery.isError
    ? '获取失败'
    : formatRuntimeStatusLabel(publishStatusQuery.data?.status)
  const shadowReadLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : (publishStatusQuery.data?.publish_pool_shadow_read ?? scheduleConfigQuery.data?.publish_pool_shadow_read)
        ? '开启'
        : '关闭'
  const killSwitchLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : (publishStatusQuery.data?.publish_pool_kill_switch ?? scheduleConfigQuery.data?.publish_pool_kill_switch)
        ? '开启'
        : '关闭'

  if (creativesQuery.isLoading && !creativesQuery.data) {
    return (
      <Flex justify="center" style={{ padding: 48 }} data-testid="creative-workbench-loading">
        <Spin size="large" />
      </Flex>
    )
  }

  if (creativesQuery.isError) {
    return (
      <PageContainer
        title="作品工作台"
        subTitle="当前无法加载作品列表，请重试或先回到运行总览。"
      >
        <div data-testid="creative-workbench-error">
          <Result
            status="error"
            title="作品列表暂时不可用"
            subTitle="列表加载失败，当前无法继续筛选、审核或进入作品详情。"
            extra={[
              <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={handleRetryPrimary}>
                重试加载
              </Button>,
              <Button key="dashboard" onClick={() => navigate('/dashboard')}>
                查看运行总览
              </Button>,
              <Button key="create" type="primary" onClick={() => void handleCreateCreative()}>
                新建作品
              </Button>,
            ]}
          />
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title="作品工作台"
      subTitle="集中处理作品创建、创作 brief、素材编排、审核与 AIClip 主流程。"
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <WorkbenchSummaryCard
          creativeFlowLabel={creativeFlowMeta.label}
          showDiagnosticsNotice={publishStatusQuery.isError || scheduleConfigQuery.isError}
          summary={summary}
          onOpenDiagnostics={handleOpenDiagnostics}
        />

        {summary.all_count === 0 ? (
          <Card data-testid="creative-workbench-empty">
            <CreativeEmptyState
              mode={creativeFlowMode}
              onCreateCreative={() => void handleCreateCreative()}
            />
          </Card>
        ) : (
          <WorkbenchTable
            formRef={formRef}
            appliedFormValues={appliedFormValues}
            appliedQueryState={appliedQueryState}
            dataSource={rows}
            loading={creativesQuery.isLoading}
            total={total}
            presetBar={(
              <WorkbenchPresetBar
                appliedPreset={appliedQueryState.preset}
                counts={workbenchPresetCounts}
                onPresetChange={handlePresetChange}
              />
            )}
            emptyState="当前筛选条件下暂无结果"
            createPending={createCreative.isPending}
            onApplyFilters={handleApplyFilters}
            onResetFilters={handleResetFilters}
            onPaginationChange={handlePaginationChange}
            onSortChange={handleSortChange}
            onCreateCreative={() => void handleCreateCreative()}
            onOpenDashboard={() => navigate('/dashboard')}
            onOpenCreativeDetail={openCreativeDetail}
          />
        )}
      </Space>

      <WorkbenchDiagnosticsDrawer
        open={diagnosticsOpen}
        onClose={handleCloseDiagnostics}
        hasDiagnosticsError={publishStatusQuery.isError || scheduleConfigQuery.isError}
        onRetryAuxiliary={handleRetryAuxiliary}
        creativeFlowDescription={creativeFlowMeta.description}
        creativeFlowLabel={creativeFlowMeta.label}
        creativeFlowShadowCompare={creativeFlowShadowCompare}
        schedulerModeLabel={schedulerModeLabel}
        effectiveSchedulerModeLabel={effectiveSchedulerModeLabel}
        runtimeStatusLabel={runtimeStatusLabel}
        shadowReadLabel={shadowReadLabel}
        killSwitchLabel={killSwitchLabel}
        activePoolCount={summary.active_pool_count}
        alignedPoolCount={summary.aligned_pool_count}
      />
    </PageContainer>
  )
}
