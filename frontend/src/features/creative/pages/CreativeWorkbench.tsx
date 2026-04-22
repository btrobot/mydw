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
import {
  creativeFlowModeMeta,
  resolveCreativeFlowMode,
  resolveCreativeFlowShadowCompare,
} from '../creativeFlow'
import {
  useCreatives,
  useCreateCreative,
  usePublishPoolItems,
  usePublishStatus,
  useScheduleConfig,
} from '../hooks/useCreatives'
import { useSystemConfig } from '@/hooks/useSystem'
import type {
  CreativeWorkbenchItem,
  CreativeWorkbenchPoolState,
  PublishPoolItem,
} from '../types/creative'
import {
  creativeStatusMeta,
  creativeWorkbenchPoolStateMeta,
  formatCreativeTimestamp,
  formatModeLabel,
  formatRuntimeStatusLabel,
  getCreativeWorkbenchPoolState,
  isPoolVersionAligned,
} from '../types/creative'

const { Paragraph, Text } = Typography

const WORKBENCH_WINDOW_SIZE = 200
const DEFAULT_WORKBENCH_PAGE_SIZE = 10

type WorkbenchSortKind = 'updated_desc' | 'updated_asc' | 'attention_desc' | 'failed_desc'
type WorkbenchPresetKey = 'all' | 'waiting_review' | 'needs_rework' | 'recent_failures' | 'version_mismatch'

type WorkbenchTableRow = CreativeWorkbenchItem & {
  poolItem: PublishPoolItem | null
  poolState: CreativeWorkbenchPoolState
  poolAligned: boolean
  hasRecentFailure: boolean
  attentionScore: number
}

type WorkbenchFormValues = {
  keyword?: string
  status?: keyof typeof creativeStatusMeta
  poolState?: CreativeWorkbenchPoolState
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
    preset,
    sort: parseWorkbenchSortKind(searchParams.get('sort')),
  }
}

const buildWorkbenchSearchParams = (
  params: WorkbenchFormValues,
  sort: WorkbenchSortKind,
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
  const creativesQuery = useCreatives({ limit: WORKBENCH_WINDOW_SIZE })
  const createCreative = useCreateCreative()
  const poolQuery = usePublishPoolItems({
    limit: WORKBENCH_WINDOW_SIZE,
    status: 'active',
  })
  const publishStatusQuery = usePublishStatus()
  const scheduleConfigQuery = useScheduleConfig()
  const systemConfigQuery = useSystemConfig()

  const items = creativesQuery.data?.items ?? []
  const total = creativesQuery.data?.total ?? 0
  const activePoolItems = poolQuery.data?.items ?? []

  const poolByCreativeId = useMemo(
    () => new Map<number, PublishPoolItem>(activePoolItems.map((item) => [item.creative_item_id, item])),
    [activePoolItems],
  )

  const alignedPoolCount = useMemo(
    () => activePoolItems.filter((item) => isPoolVersionAligned(item)).length,
    [activePoolItems],
  )

  const waitingReviewCount = useMemo(
    () => items.filter((item) => item.status === 'WAITING_REVIEW').length,
    [items],
  )

  const pendingInputCount = useMemo(
    () => items.filter((item) => item.status === 'PENDING_INPUT').length,
    [items],
  )

  const schedulerMode = publishStatusQuery.data?.scheduler_mode ?? scheduleConfigQuery.data?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatusQuery.data?.effective_scheduler_mode ?? schedulerMode
  const creativeFlowMode = resolveCreativeFlowMode(systemConfigQuery.data)
  const creativeFlowShadowCompare = resolveCreativeFlowShadowCompare(systemConfigQuery.data)
  const creativeFlowMeta = creativeFlowModeMeta[creativeFlowMode]

  const rows = useMemo<WorkbenchTableRow[]>(
    () => items.map((item) => {
      const poolItem = poolByCreativeId.get(item.id) ?? null
      const poolState = getCreativeWorkbenchPoolState(poolItem)
      const hasRecentFailure = Boolean(item.generation_error_msg || item.status === 'FAILED' || item.generation_failed_at)
      return {
        ...item,
        poolItem,
        poolState,
        poolAligned: poolItem ? isPoolVersionAligned(poolItem) : false,
        hasRecentFailure,
        attentionScore: getAttentionScore(item, poolState),
      }
    }),
    [items, poolByCreativeId],
  )

  const workbenchPresetCounts = useMemo(
    () => ({
      all: rows.length,
      waiting_review: rows.filter((item) => item.status === 'WAITING_REVIEW').length,
      needs_rework: rows.filter((item) => item.status === 'REWORK_REQUIRED').length,
      recent_failures: rows.filter((item) => item.hasRecentFailure).length,
      version_mismatch: rows.filter((item) => item.poolState === 'version_mismatch').length,
    }),
    [rows],
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
      poolQuery.refetch(),
      publishStatusQuery.refetch(),
      scheduleConfigQuery.refetch(),
      systemConfigQuery.refetch(),
    ])
  }, [poolQuery, publishStatusQuery, scheduleConfigQuery, systemConfigQuery])

  const handleCreateCreative = useCallback(async () => {
    try {
      const created = await createCreative.mutateAsync({})
      message.success('已创建空白作品，请继续补齐素材与配置')
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
    const nextSearchParams = buildWorkbenchSearchParams(nextPresetState, nextPresetState.sort)
    formRef.current?.setFieldsValue({
      keyword: nextPresetState.keyword,
      status: nextPresetState.status,
      poolState: nextPresetState.poolState,
    })
    setSearchParams(nextSearchParams, { replace: true })
    actionRef.current?.setPageInfo?.({ current: 1, pageSize: nextPresetState.pageSize })
    actionRef.current?.reload()
  }, [initialRouteState.pageSize, setSearchParams])

  const handleSortChange = useCallback((sort: WorkbenchSortKind) => {
    const currentFormValues = formRef.current?.getFieldsValue?.() ?? {}
    const nextSearchParams = buildWorkbenchSearchParams(
      {
        keyword: currentFormValues.keyword,
        status: currentFormValues.status,
        poolState: currentFormValues.poolState,
        preset: initialRouteState.preset,
        current: 1,
        pageSize: initialRouteState.pageSize,
      },
      sort,
    )
    setSearchParams(nextSearchParams, { replace: true })
    actionRef.current?.setPageInfo?.({ current: 1, pageSize: initialRouteState.pageSize })
    actionRef.current?.reload()
  }, [initialRouteState.pageSize, initialRouteState.preset, setSearchParams])

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
        title: '作品标题',
        dataIndex: 'title',
        ellipsis: true,
        hideInSearch: true,
        render: (_, record) => (
          <Space direction="vertical" size={4}>
            <Text strong>{record.title?.trim() || record.creative_no}</Text>
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
              {record.poolItem ? (
                <Tag color={record.poolAligned ? 'success' : 'warning'}>
                  池版本 #{record.poolItem.creative_version_id}
                </Tag>
              ) : null}
            </Space>
            <Text type="secondary">
              {record.poolItem ? `发布池记录 #${record.poolItem.id}` : '当前版本尚未进入发布池'}
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
              详情
            </Button>
            <Button
              type="link"
              onClick={() => openCreativeDetail(record.id)}
              disabled={!record.current_version_id}
              data-testid={`creative-workbench-open-review-${record.id}`}
            >
              审核
            </Button>
            <Button
              type="link"
              icon={<ArrowRightOutlined />}
              onClick={() => openCreativeDetail(record.id, { tool: 'ai-clip' })}
              disabled={!record.current_version_id}
              data-testid={`creative-workbench-ai-clip-${record.id}`}
            >
              AIClip
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
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (creativesQuery.isError) {
    return (
      <PageContainer
        title="作品工作台"
      subTitle="当前无法加载作品列表，请先恢复主业务入口，再进入筛选与处理流程。"
      >
        <div data-testid="creative-workbench-error">
          <Result
            status="error"
            title="作品列表暂时不可用"
            subTitle="作品工作台没有拿到列表数据，当前不能继续把失败状态误当成空白工作台。"
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
      subTitle="先创建作品，再补齐素材、合成配置与执行动作；任务管理只承接执行记录、失败重试与排障。"
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        {(publishStatusQuery.isError || scheduleConfigQuery.isError) && (
          <Alert
            type="warning"
            showIcon
            message="发布运行摘要暂时不可用"
            description="发布状态或调度配置加载失败，当前摘要仅展示已成功拿到的数据，不会把失败伪装成正常空闲。"
            action={(
              <Button size="small" icon={<ReloadOutlined />} onClick={handleRetryAuxiliary}>
                重试
              </Button>
            )}
            data-testid="creative-workbench-runtime-warning"
          />
        )}

        {poolQuery.isError && (
          <Alert
            type="warning"
            showIcon
            message="发布池摘要暂时不可用"
            description="发布池请求失败，已暂停展示对齐统计，请稍后重试。"
            action={(
              <Button size="small" icon={<ReloadOutlined />} onClick={handleRetryAuxiliary}>
                重试
              </Button>
            )}
            data-testid="creative-workbench-pool-warning"
          />
        )}

        <Card data-testid="creative-workbench-publish-summary">
          <Flex wrap gap={24}>
            <Statistic title="作品数" value={total} />
            <Statistic title="待审核" value={waitingReviewCount} />
            <Statistic title="待补充" value={pendingInputCount} />
            <Statistic
              title="已进发布池"
              value={poolQuery.isError ? '—' : poolQuery.data?.total ?? 0}
              loading={poolQuery.isLoading && !poolQuery.isError}
            />
            <Statistic
              title="池版本已对齐"
              value={poolQuery.isError ? '—' : alignedPoolCount}
              loading={poolQuery.isLoading && !poolQuery.isError}
            />
          </Flex>

          <Space wrap size={[8, 8]} style={{ marginTop: 16 }}>
            <Tag data-testid="creative-workbench-main-entry-banner">入口模式：{creativeFlowMeta.label}</Tag>
            <Tag data-testid="creative-workbench-shadow-compare">
              Shadow Compare：{creativeFlowShadowCompare ? '开启' : '关闭'}
            </Tag>
            <Tag data-testid="creative-workbench-scheduler-mode">配置模式：{schedulerModeLabel}</Tag>
            <Tag data-testid="creative-workbench-effective-mode">生效模式：{effectiveSchedulerModeLabel}</Tag>
            <Tag data-testid="creative-workbench-runtime-status">运行状态：{runtimeStatusLabel}</Tag>
            <Tag data-testid="creative-workbench-shadow-read">Shadow Read：{shadowReadLabel}</Tag>
            <Tag data-testid="creative-workbench-kill-switch">Kill Switch：{killSwitchLabel}</Tag>
          </Space>

          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            {creativeFlowMeta.description} 发布池、调度与运行状态仅作为辅助判断信息，不再占据首屏主流程。
          </Paragraph>
        </Card>

        {rows.length === 0 ? (
          <Card data-testid="creative-workbench-empty">
            <CreativeEmptyState
              mode={creativeFlowMode}
              onCreateCreative={() => void handleCreateCreative()}
            />
          </Card>
        ) : (
          <>
            {total > rows.length ? (
              <Card>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  当前工作台已加载最近 {rows.length} 条作品，本次搜索、筛选与排序基于当前窗口数据执行；若作品规模继续扩大，后续 PR 会再接入服务端检索能力。
                </Paragraph>
              </Card>
            ) : null}

            <ProTable<WorkbenchTableRow, WorkbenchFormValues>
              actionRef={actionRef}
              formRef={formRef}
              rowKey="id"
              columns={columns}
              cardBordered
              headerTitle="今日待处理作品"
              options={{ density: false, setting: false }}
              request={async (params, sort) => {
                const keyword = params.keyword?.trim().toLowerCase()
                const status = params.status
                const poolState = params.poolState as CreativeWorkbenchPoolState | undefined
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
                    preset: initialRouteState.preset,
                    current: params.current,
                    pageSize: params.pageSize,
                  },
                  sortKind,
                )

                if (nextSearchParams.toString() !== searchParams.toString()) {
                  setSearchParams(nextSearchParams, { replace: true })
                }

                let filtered = rows

                if (keyword) {
                  filtered = filtered.filter((item) =>
                    [item.title ?? '', item.creative_no]
                      .join(' ')
                      .toLowerCase()
                      .includes(keyword),
                  )
                }

                if (status) {
                  filtered = filtered.filter((item) => item.status === status)
                }

                if (poolState) {
                  filtered = filtered.filter((item) => item.poolState === poolState)
                }

                if (initialRouteState.preset === 'recent_failures') {
                  filtered = filtered.filter((item) => item.hasRecentFailure)
                }

                const sorted = [...filtered].sort((left, right) => {
                  const updatedAtDelta = Date.parse(right.updated_at) - Date.parse(left.updated_at)
                  const failedAtDelta = Date.parse(right.generation_failed_at ?? right.updated_at) - Date.parse(left.generation_failed_at ?? left.updated_at)

                  switch (sortKind) {
                    case 'updated_asc':
                      return -updatedAtDelta
                    case 'attention_desc':
                      if (right.attentionScore !== left.attentionScore) {
                        return right.attentionScore - left.attentionScore
                      }
                      return updatedAtDelta
                    case 'failed_desc':
                      if (right.hasRecentFailure !== left.hasRecentFailure) {
                        return Number(right.hasRecentFailure) - Number(left.hasRecentFailure)
                      }
                      if (right.hasRecentFailure && left.hasRecentFailure && failedAtDelta !== 0) {
                        return failedAtDelta
                      }
                      return updatedAtDelta
                    case 'updated_desc':
                    default:
                      return updatedAtDelta
                  }
                })

                const current = params.current ?? 1
                const pageSize = params.pageSize ?? 10
                const start = (current - 1) * pageSize

                return {
                  data: sorted.slice(start, start + pageSize),
                  success: true,
                  total: sorted.length,
                }
              }}
              loading={creativesQuery.isLoading || poolQuery.isLoading}
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
                emptyText: (
                  <CreativeEmptyState
                    mode={creativeFlowMode}
                    onCreateCreative={() => void handleCreateCreative()}
                  />
                ),
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
                  查看运行总览
                </Button>,
              ]}
            />
          </>
        )}
      </Space>
    </PageContainer>
  )
}
