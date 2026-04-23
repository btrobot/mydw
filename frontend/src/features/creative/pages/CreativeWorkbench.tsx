import { ArrowRightOutlined, ReloadOutlined } from '@ant-design/icons'
import { PageContainer, ProTable } from '@ant-design/pro-components'
import type { ActionType, ProColumns, ProFormInstance } from '@ant-design/pro-components'
import { useCallback, useEffect, useMemo, useRef } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Alert,
  App,
  Button,
  Card,
  Descriptions,
  Drawer,
  Flex,
  Result,
  Select,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd'

import CreativeEmptyState from '../components/CreativeEmptyState'
import { countEnabledCreativeInputItems, formatCreativeDuration } from '../creativeAuthoring'
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
  formatCreativeTimestamp,
  formatModeLabel,
  formatRuntimeStatusLabel,
} from '../types/creative'

const { Paragraph, Text } = Typography

const DEFAULT_WORKBENCH_PAGE_SIZE = 10

type WorkbenchSortKind = 'updated_desc' | 'updated_asc' | 'attention_desc' | 'failed_desc'
type WorkbenchPresetKey = 'all' | 'waiting_review' | 'needs_rework' | 'recent_failures' | 'version_mismatch'
type WorkbenchDiagnosticsView = 'runtime'

type WorkbenchTableRow = CreativeWorkbenchItem & {
  poolState: CreativeWorkbenchPoolState
  poolAligned: boolean
  hasRecentFailure: boolean
  attentionScore: number
}

type WorkbenchFormValues = {
  keyword?: string | null
  status?: keyof typeof creativeStatusMeta | null
  poolState?: CreativeWorkbenchPoolState | null
  preset?: WorkbenchPresetKey
  current?: number
  pageSize?: number
}

const creativeStatusValueEnum = Object.fromEntries(
  Object.entries(creativeStatusMeta).map(([key, value]) => [key, { text: value.label }]),
)

const creativePoolValueEnum = Object.fromEntries(
  Object.entries(creativeWorkbenchPoolStateMeta).map(([key, value]) => [key, { text: value.label }]),
) as Record<CreativeWorkbenchPoolState, { text: string }>

const workbenchSortOptions: Array<{ label: string; value: WorkbenchSortKind }> = [
  { label: '最近更新优先', value: 'updated_desc' },
  { label: '最早更新优先', value: 'updated_asc' },
  { label: '待处理优先', value: 'attention_desc' },
  { label: '最近失败优先', value: 'failed_desc' },
]

const workbenchPresetMeta: Record<WorkbenchPresetKey, { label: string }> = {
  all: { label: '全部' },
  waiting_review: { label: '待审核' },
  needs_rework: { label: '需返工' },
  recent_failures: { label: '最近失败' },
  version_mismatch: { label: '版本未对齐' },
}

const defaultWorkbenchSummary = {
  all_count: 0,
  waiting_review_count: 0,
  pending_input_count: 0,
  needs_rework_count: 0,
  recent_failures_count: 0,
  active_pool_count: 0,
  aligned_pool_count: 0,
  version_mismatch_count: 0,
}

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
  value && value in workbenchPresetMeta ? value as WorkbenchPresetKey : undefined

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
): { keyword?: string; status?: keyof typeof creativeStatusMeta; poolState?: CreativeWorkbenchPoolState; sort: WorkbenchSortKind; current: number; pageSize: number; preset: WorkbenchPresetKey } => {
  switch (preset) {
    case 'waiting_review':
      return { preset, status: 'WAITING_REVIEW', sort: 'updated_desc', current: 1, pageSize }
    case 'needs_rework':
      return { preset, status: 'REWORK_REQUIRED', sort: 'updated_desc', current: 1, pageSize }
    case 'recent_failures':
      return { preset, sort: 'failed_desc', current: 1, pageSize }
    case 'version_mismatch':
      return { preset, poolState: 'version_mismatch', sort: 'attention_desc', current: 1, pageSize }
    case 'all':
    default:
      return { preset: 'all', sort: 'updated_desc', current: 1, pageSize }
  }
}

const parseWorkbenchStateFromSearchParams = (searchParams: URLSearchParams) => {
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
    formValues: {
      keyword,
      status,
      poolState,
      preset,
    } satisfies WorkbenchFormValues,
    current: parsePositiveInteger(searchParams.get('page'), 1),
    pageSize: parsePositiveInteger(searchParams.get('pageSize'), DEFAULT_WORKBENCH_PAGE_SIZE),
    diagnostics,
    preset,
    sort: parseWorkbenchSortKind(searchParams.get('sort')),
  }
}

const buildWorkbenchSearchParams = (
  params: WorkbenchFormValues,
  sort: WorkbenchSortKind,
  diagnostics?: WorkbenchDiagnosticsView,
): URLSearchParams => {
  const nextSearchParams = new URLSearchParams()
  const keyword = params.keyword?.trim()

  if (keyword) {
    nextSearchParams.set('keyword', keyword)
  }

  if (params.status) {
    nextSearchParams.set('status', params.status)
  }

  if (params.poolState) {
    nextSearchParams.set('poolState', params.poolState)
  }

  const preset = isPresetCompatible(params.preset, params, sort) ? params.preset : undefined

  if (preset) {
    nextSearchParams.set('preset', preset)
  }

  nextSearchParams.set('sort', sort)
  nextSearchParams.set('page', String(params.current ?? 1))
  nextSearchParams.set('pageSize', String(params.pageSize ?? DEFAULT_WORKBENCH_PAGE_SIZE))

  if (diagnostics) {
    nextSearchParams.set('diagnostics', diagnostics)
  }

  return nextSearchParams
}

export default function CreativeWorkbench() {
  const location = useLocation()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { message } = App.useApp()
  const actionRef = useRef<ActionType>()
  const formRef = useRef<ProFormInstance<WorkbenchFormValues>>()
  const initialRouteState = useMemo(
    () => parseWorkbenchStateFromSearchParams(searchParams),
    [searchParams],
  )
  const creativesQuery = useCreatives({
    skip: (initialRouteState.current - 1) * initialRouteState.pageSize,
    limit: initialRouteState.pageSize,
    keyword: initialRouteState.formValues.keyword,
    status: initialRouteState.formValues.status,
    poolState: initialRouteState.formValues.poolState,
    sort: initialRouteState.sort,
    recentFailuresOnly: initialRouteState.preset === 'recent_failures',
  })
  const createCreative = useCreateCreative()
  const publishStatusQuery = usePublishStatus()
  const scheduleConfigQuery = useScheduleConfig()
  const systemConfigQuery = useSystemConfig()

  const items = creativesQuery.data?.items ?? []
  const total = creativesQuery.data?.total ?? 0
  const summary = creativesQuery.data?.summary ?? defaultWorkbenchSummary
  const diagnosticsOpen = initialRouteState.diagnostics === 'runtime'

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
    if (!creativesQuery.isLoading) {
      actionRef.current?.reload()
    }
  }, [creativesQuery.isLoading, rows])

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

  const handlePresetChange = useCallback((preset: WorkbenchPresetKey) => {
    const nextPresetState = getPresetState(preset, initialRouteState.pageSize)
    const nextSearchParams = buildWorkbenchSearchParams(
      nextPresetState,
      nextPresetState.sort,
      initialRouteState.diagnostics,
    )
    formRef.current?.setFieldsValue({
      keyword: nextPresetState.keyword ?? '',
      status: nextPresetState.status ?? null,
      poolState: nextPresetState.poolState ?? null,
      preset: nextPresetState.preset,
    })
    setSearchParams(nextSearchParams, { replace: true })
    actionRef.current?.setPageInfo?.({ current: 1, pageSize: nextPresetState.pageSize })
    actionRef.current?.reload()
  }, [initialRouteState.diagnostics, initialRouteState.pageSize, setSearchParams])

  const handleSortChange = useCallback((sort: WorkbenchSortKind) => {
    const nextSearchParams = buildWorkbenchSearchParams(
      {
        keyword: initialRouteState.formValues.keyword,
        status: initialRouteState.formValues.status,
        poolState: initialRouteState.formValues.poolState,
        preset: initialRouteState.formValues.preset,
        current: 1,
        pageSize: initialRouteState.pageSize,
      },
      sort,
      initialRouteState.diagnostics,
    )
    setSearchParams(nextSearchParams, { replace: true })
    actionRef.current?.setPageInfo?.({ current: 1, pageSize: initialRouteState.pageSize })
    actionRef.current?.reload()
  }, [initialRouteState.diagnostics, initialRouteState.formValues.keyword, initialRouteState.formValues.poolState, initialRouteState.formValues.preset, initialRouteState.formValues.status, initialRouteState.pageSize, setSearchParams])

  const setDiagnosticsView = useCallback((diagnostics?: WorkbenchDiagnosticsView) => {
    const nextSearchParams = buildWorkbenchSearchParams(
      {
        keyword: initialRouteState.formValues.keyword,
        status: initialRouteState.formValues.status,
        poolState: initialRouteState.formValues.poolState,
        preset: initialRouteState.formValues.preset,
        current: initialRouteState.current,
        pageSize: initialRouteState.pageSize,
      },
      initialRouteState.sort,
      diagnostics,
    )
    setSearchParams(nextSearchParams, { replace: true })
  }, [
    initialRouteState.current,
    initialRouteState.pageSize,
    initialRouteState.formValues.keyword,
    initialRouteState.formValues.poolState,
    initialRouteState.formValues.preset,
    initialRouteState.formValues.status,
    initialRouteState.sort,
    setSearchParams,
  ])

  const handleOpenDiagnostics = useCallback(() => {
    setDiagnosticsView('runtime')
  }, [setDiagnosticsView])

  const handleCloseDiagnostics = useCallback(() => {
    setDiagnosticsView(undefined)
  }, [setDiagnosticsView])

  const columns = useMemo<ProColumns<WorkbenchTableRow>[]>(
    () => [
      {
        title: '作品检索',
        dataIndex: 'keyword',
        hideInTable: true,
        fieldProps: {
          placeholder: '按标题或作品编号搜索',
          allowClear: true,
          'data-testid': 'creative-workbench-search-input',
        },
      },
      {
        title: '作品编号',
        dataIndex: 'creative_no',
        width: 160,
        hideInSearch: true,
        render: (_, record) => (
          <Space direction="vertical" size={2}>
            <Text strong>{record.creative_no}</Text>
            <Text type="secondary">#{record.id}</Text>
          </Space>
        ),
      },
      {
        title: '作品 / 创作定义',
        dataIndex: 'title',
        ellipsis: true,
        hideInSearch: true,
        render: (_, record) => (
          <Space direction="vertical" size={4}>
            <Text strong>{record.title?.trim() || record.creative_no}</Text>
            <Text type="secondary">
              {[
                record.subject_product_name_snapshot || undefined,
                formatCreativeDuration(record.target_duration_seconds),
                `${countEnabledCreativeInputItems(record.input_items)} 个编排项`,
              ]
                .filter(Boolean)
                .join(' · ')}
            </Text>
            {record.main_copywriting_text?.trim() ? (
              <Text type="secondary" ellipsis={{ tooltip: record.main_copywriting_text }}>
                主文案：{record.main_copywriting_text}
              </Text>
            ) : null}
            {record.generation_error_msg ? (
              <Text type="warning">最近一次生成回填失败</Text>
            ) : (
              <Text type="secondary">当前版本 #{record.current_version_id ?? '-'}</Text>
            )}
          </Space>
        ),
      },
      {
        title: '作品状态',
        dataIndex: 'status',
        width: 140,
        valueType: 'select',
        valueEnum: creativeStatusValueEnum,
        fieldProps: {
          placeholder: '按作品状态筛选',
          allowClear: true,
          'data-testid': 'creative-workbench-status-filter',
        },
        render: (_, record) => {
          const statusMeta = creativeStatusMeta[record.status]
          return <Tag color={statusMeta.color}>{statusMeta.label}</Tag>
        },
      },
      {
        title: '发布准备',
        dataIndex: 'poolState',
        width: 220,
        valueType: 'select',
        valueEnum: creativePoolValueEnum,
        fieldProps: {
          placeholder: '按发布准备筛选',
          allowClear: true,
          'data-testid': 'creative-workbench-pool-filter',
        },
        render: (_, record) => (
          <Space direction="vertical" size={4} data-testid={`creative-workbench-pool-state-${record.id}`}>
            <Space wrap size={[4, 4]}>
              <Tag color={creativeWorkbenchPoolStateMeta[record.poolState].color}>
                {creativeWorkbenchPoolStateMeta[record.poolState].label}
              </Tag>
              {record.active_pool_version_id ? (
                <Tag color={record.poolAligned ? 'success' : 'warning'}>
                  池版本 #{record.active_pool_version_id}
                </Tag>
              ) : null}
            </Space>
            <Text type="secondary">
              {record.active_pool_item_id ? `发布池记录 #${record.active_pool_item_id}` : '当前版本尚未进入发布池'}
            </Text>
          </Space>
        ),
      },
      {
        title: '更新时间',
        dataIndex: 'updated_at',
        width: 180,
        hideInSearch: true,
        render: (_, record) => formatCreativeTimestamp(record.updated_at),
      },
      {
        title: '操作',
        key: 'actions',
        width: 220,
        hideInSearch: true,
        render: (_, record) => (
          <Space size={0} wrap>
            <Button
              type="link"
              onClick={() => openCreativeDetail(record.id)}
              data-testid={`creative-workbench-open-detail-${record.id}`}
            >
              查看作品
            </Button>
            <Button
              type="link"
              onClick={() => openCreativeDetail(record.id)}
              disabled={!record.current_version_id}
              data-testid={`creative-workbench-open-review-${record.id}`}
            >
              审核当前版本
            </Button>
            <Button
              type="link"
              icon={<ArrowRightOutlined />}
              onClick={() => openCreativeDetail(record.id, { tool: 'ai-clip' })}
              disabled={!record.current_version_id}
              data-testid={`creative-workbench-ai-clip-${record.id}`}
            >
              进入 AIClip
            </Button>
          </Space>
        ),
      },
    ],
    [openCreativeDetail],
  )

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
        <Card data-testid="creative-workbench-publish-summary">
          <Flex justify="space-between" align="start" gap={16} wrap="wrap">
            <Space direction="vertical" size={4}>
              <Text type="secondary" data-testid="creative-workbench-main-entry-banner">
                入口模式：{creativeFlowMeta.label}
              </Text>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                默认先处理作品 brief、素材编排、审核与 AIClip；运行侧信息请从“查看运行诊断”进入。
              </Paragraph>
            </Space>
            <Button onClick={handleOpenDiagnostics} data-testid="creative-workbench-open-diagnostics">
              查看运行诊断
            </Button>
          </Flex>

          {(publishStatusQuery.isError || scheduleConfigQuery.isError) && (
            <Alert
              type="warning"
              showIcon
              message="部分运行诊断暂不可用，可通过“查看运行诊断”重试。"
              description="当前不影响作品主流程，可稍后进入诊断抽屉重试。"
              style={{ marginTop: 16 }}
              data-testid="creative-workbench-diagnostics-notice"
            />
          )}

          <Flex wrap gap={24}>
            <Statistic title="作品数" value={summary.all_count} />
            <Statistic title="待审核" value={summary.waiting_review_count} />
            <Statistic title="待补充" value={summary.pending_input_count} />
            <Statistic title="已进发布池" value={summary.active_pool_count} />
            <Statistic title="池版本已对齐" value={summary.aligned_pool_count} />
          </Flex>
        </Card>

        {summary.all_count === 0 ? (
          <Card data-testid="creative-workbench-empty">
            <CreativeEmptyState
              mode={creativeFlowMode}
              onCreateCreative={() => void handleCreateCreative()}
            />
          </Card>
        ) : (
          <>
            <ProTable<WorkbenchTableRow, WorkbenchFormValues>
              key={searchParams.toString()}
              actionRef={actionRef}
              formRef={formRef}
              rowKey="id"
              columns={columns}
              cardBordered
              headerTitle="待处理作品"
              options={{ density: false, setting: false }}
              request={async (params, sort) => {
                const status = params.status ?? undefined
                const poolState = (params.poolState ?? undefined) as CreativeWorkbenchPoolState | undefined
                const currentFormValues = formRef.current?.getFieldsValue?.() ?? {}
                const sortKind = sort.updated_at === 'ascend'
                  ? 'updated_asc'
                  : sort.updated_at === 'descend'
                    ? 'updated_desc'
                    : initialRouteState.sort
                const nextSearchParams = buildWorkbenchSearchParams(
                  {
                    keyword: params.keyword,
                    status,
                    poolState,
                    preset: params.preset ?? currentFormValues.preset,
                    current: params.current,
                    pageSize: params.pageSize,
                  },
                  sortKind,
                  initialRouteState.diagnostics,
                )

                if (nextSearchParams.toString() !== searchParams.toString()) {
                  setSearchParams(nextSearchParams, { replace: true })
                }

                return {
                  data: rows,
                  success: true,
                  total,
                }
              }}
              loading={creativesQuery.isLoading}
              pagination={{
                current: initialRouteState.current,
                pageSize: initialRouteState.pageSize,
                showSizeChanger: true,
                showTotal: (count) => `共 ${count} 条作品`,
              }}
              form={{
                initialValues: initialRouteState.formValues,
              }}
              search={{
                labelWidth: 'auto',
                defaultCollapsed: false,
                searchText: '应用筛选',
                resetText: '重置筛选',
              }}
              tableExtraRender={() => (
                <Space direction="vertical" style={{ width: '100%' }} size={12}>
                  <Space wrap>
                    <Text type="secondary">高频视角：</Text>
                    {(Object.keys(workbenchPresetMeta) as WorkbenchPresetKey[]).map((preset) => (
                      <Button
                        key={preset}
                        size="small"
                        type={initialRouteState.preset === preset || (!initialRouteState.preset && preset === 'all') ? 'primary' : 'default'}
                        onClick={() => handlePresetChange(preset)}
                        data-testid={`creative-workbench-preset-${preset}`}
                      >
                        {workbenchPresetMeta[preset].label}（{workbenchPresetCounts[preset]}）
                      </Button>
                    ))}
                  </Space>
                </Space>
              )}
              locale={{
                emptyText: summary.all_count === 0
                  ? (
                    <CreativeEmptyState
                      mode={creativeFlowMode}
                      onCreateCreative={() => void handleCreateCreative()}
                    />
                  )
                  : '当前筛选条件下暂无结果',
              }}
              toolBarRender={() => [
                <div key="sort" data-testid="creative-workbench-sort-select">
                  <Select
                    value={initialRouteState.sort}
                    options={workbenchSortOptions}
                    style={{ width: 180 }}
                    onChange={(value) => handleSortChange(value)}
                  />
                </div>,
                <Button
                  key="create"
                  type="primary"
                  loading={createCreative.isPending}
                  onClick={() => void handleCreateCreative()}
                  data-testid="creative-workbench-create"
                >
                  新建作品
                </Button>,
                <Button
                  key="dashboard"
                  onClick={() => navigate('/dashboard')}
                  data-testid="creative-workbench-open-dashboard"
                >
                  运行总览
                </Button>,
              ]}
            />
          </>
        )}
      </Space>

      <Drawer
        title="运行诊断"
        open={diagnosticsOpen}
        onClose={handleCloseDiagnostics}
        destroyOnClose
        width={520}
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }} data-testid="creative-workbench-diagnostics-drawer">
          {(publishStatusQuery.isError || scheduleConfigQuery.isError) && (
            <Alert
              type="warning"
              showIcon
              message="发布运行诊断暂时不可用"
              description="发布状态或调度配置加载失败，当前不能把失败伪装成空闲状态。"
              action={(
                <Button size="small" icon={<ReloadOutlined />} onClick={handleRetryAuxiliary}>
                  重试
                </Button>
              )}
              data-testid="creative-workbench-runtime-warning"
            />
          )}

          <Card size="small" title="运行态摘要">
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="入口模式">
                <Space wrap>
                  <Tag data-testid="creative-workbench-main-entry-diagnostics">{creativeFlowMeta.label}</Tag>
                  <Tag data-testid="creative-workbench-shadow-compare">
                    Shadow Compare：{creativeFlowShadowCompare ? '开启' : '关闭'}
                  </Tag>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="配置模式">
                <Tag data-testid="creative-workbench-scheduler-mode">{schedulerModeLabel}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="生效模式">
                <Tag data-testid="creative-workbench-effective-mode">{effectiveSchedulerModeLabel}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="运行状态">
                <Tag data-testid="creative-workbench-runtime-status">{runtimeStatusLabel}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Shadow Read">
                <Tag data-testid="creative-workbench-shadow-read">{shadowReadLabel}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Kill Switch">
                <Tag data-testid="creative-workbench-kill-switch">{killSwitchLabel}</Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Card size="small" title="发布池诊断">
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="已进发布池">
                {summary.active_pool_count}
              </Descriptions.Item>
              <Descriptions.Item label="池版本已对齐">
                {summary.aligned_pool_count}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {creativeFlowMeta.description} 这里仅保留运行排障与发布池观察信息。
          </Paragraph>
        </Space>
      </Drawer>
    </PageContainer>
  )
}
