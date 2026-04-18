import { ArrowRightOutlined } from '@ant-design/icons'
import { PageContainer, ProTable } from '@ant-design/pro-components'
import type { ActionType, ProColumns } from '@ant-design/pro-components'
import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Flex,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd'

import CreativeEmptyState from '../components/CreativeEmptyState'
import {
  useCreatives,
  usePublishPoolItems,
  usePublishStatus,
  useScheduleConfig,
} from '../hooks/useCreatives'
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

type WorkbenchTableRow = CreativeWorkbenchItem & {
  poolItem: PublishPoolItem | null
  poolState: CreativeWorkbenchPoolState
  poolAligned: boolean
}

const creativeStatusValueEnum = Object.fromEntries(
  Object.entries(creativeStatusMeta).map(([key, value]) => [key, { text: value.label }]),
)

const creativePoolValueEnum = Object.fromEntries(
  Object.entries(creativeWorkbenchPoolStateMeta).map(([key, value]) => [key, { text: value.label }]),
) as Record<CreativeWorkbenchPoolState, { text: string }>

export default function CreativeWorkbench() {
  const navigate = useNavigate()
  const actionRef = useRef<ActionType>()
  const { data, isLoading } = useCreatives({ limit: WORKBENCH_WINDOW_SIZE })
  const { data: poolData, isLoading: poolLoading } = usePublishPoolItems({
    limit: WORKBENCH_WINDOW_SIZE,
    status: 'active',
  })
  const { data: publishStatus } = usePublishStatus()
  const { data: scheduleConfig } = useScheduleConfig()

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const activePoolItems = poolData?.items ?? []

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

  const schedulerMode = publishStatus?.scheduler_mode ?? scheduleConfig?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatus?.effective_scheduler_mode ?? schedulerMode

  const rows = useMemo<WorkbenchTableRow[]>(
    () => items.map((item) => {
      const poolItem = poolByCreativeId.get(item.id) ?? null
      return {
        ...item,
        poolItem,
        poolState: getCreativeWorkbenchPoolState(poolItem),
        poolAligned: poolItem ? isPoolVersionAligned(poolItem) : false,
      }
    }),
    [items, poolByCreativeId],
  )

  useEffect(() => {
    if (!isLoading) {
      actionRef.current?.reload()
    }
  }, [isLoading, rows])

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
              <Text type="warning">最近一次生成回写失败</Text>
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
        sorter: true,
        defaultSortOrder: 'descend',
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
              onClick={() => navigate(`/creative/${record.id}`)}
              data-testid={`creative-workbench-open-detail-${record.id}`}
            >
              详情
            </Button>
            <Button
              type="link"
              onClick={() => navigate(`/creative/${record.id}`)}
              disabled={!record.current_version_id}
              data-testid={`creative-workbench-open-review-${record.id}`}
            >
              审核
            </Button>
            <Button
              type="link"
              icon={<ArrowRightOutlined />}
              onClick={() => navigate(`/creative/${record.id}?tool=ai-clip`)}
              disabled={!record.current_version_id}
              data-testid={`creative-workbench-ai-clip-${record.id}`}
            >
              AIClip
            </Button>
          </Space>
        ),
      },
    ],
    [navigate],
  )

  if (isLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  return (
    <PageContainer
      title="作品工作台"
      subTitle="搜索、筛选并处理当天作品；运行总览与任务诊断继续作为辅助入口保留"
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Card data-testid="creative-workbench-publish-summary">
          <Flex wrap gap={24}>
            <Statistic title="作品数" value={total} />
            <Statistic title="待审核" value={waitingReviewCount} />
            <Statistic title="待补充" value={pendingInputCount} />
            <Statistic title="已进发布池" value={poolData?.total ?? 0} loading={poolLoading} />
            <Statistic title="池版本已对齐" value={alignedPoolCount} loading={poolLoading} />
          </Flex>

          <Space wrap size={[8, 8]} style={{ marginTop: 16 }}>
            <Tag data-testid="creative-workbench-main-entry-banner">默认业务入口：作品工作台</Tag>
            <Tag data-testid="creative-workbench-scheduler-mode">配置模式：{formatModeLabel(schedulerMode)}</Tag>
            <Tag data-testid="creative-workbench-effective-mode">生效模式：{formatModeLabel(effectiveSchedulerMode)}</Tag>
            <Tag data-testid="creative-workbench-runtime-status">
              运行状态：{formatRuntimeStatusLabel(publishStatus?.status)}
            </Tag>
            <Tag data-testid="creative-workbench-shadow-read">
              影子读取（Shadow Read）：{publishStatus?.publish_pool_shadow_read ? '开启' : '关闭'}
            </Tag>
            <Tag data-testid="creative-workbench-kill-switch">
              熔断开关（Kill Switch）：{publishStatus?.publish_pool_kill_switch ? '开启' : '关闭'}
            </Tag>
          </Space>

          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            先在这里搜索、筛选并安排当天要处理的作品；发布池、调度与运行状态仅作为辅助判断信息，不再占据首屏主流程。
          </Paragraph>
        </Card>

        {total > rows.length ? (
          <Card>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              当前工作台已加载最近 {rows.length} 条作品，本次搜索、筛选与排序基于当前窗口数据执行；若作品规模继续扩大，后续 PR 会再接入服务端检索能力。
            </Paragraph>
          </Card>
        ) : null}

        <ProTable<WorkbenchTableRow, { keyword?: string; status?: string; poolState?: string }>
          actionRef={actionRef}
          rowKey="id"
          columns={columns}
          cardBordered
          headerTitle="今日待处理作品"
          options={{ density: false, setting: false }}
          request={async (params, sort) => {
            const keyword = params.keyword?.trim().toLowerCase()
            const status = params.status
            const poolState = params.poolState as CreativeWorkbenchPoolState | undefined

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

            const updatedAtSort = sort.updated_at
            const sorted = [...filtered].sort((left, right) => {
              const delta = Date.parse(left.updated_at) - Date.parse(right.updated_at)

              if (updatedAtSort === 'ascend') {
                return delta
              }

              return -delta
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
          loading={isLoading || poolLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (count) => `共 ${count} 条作品`,
          }}
          search={{
            labelWidth: 'auto',
            defaultCollapsed: false,
            searchText: '应用筛选',
            resetText: '重置筛选',
          }}
          locale={{
            emptyText: <CreativeEmptyState onOpenTaskList={() => navigate('/task/list')} />,
          }}
          toolBarRender={() => [
            <Button key="dashboard" onClick={() => navigate('/dashboard')}>
              查看运行总览
            </Button>,
            <Button key="task-list" onClick={() => navigate('/task/list')}>
              查看任务诊断
            </Button>,
          ]}
        />
      </Space>
    </PageContainer>
  )
}
