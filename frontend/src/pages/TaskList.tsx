import { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import dayjs, { type Dayjs } from 'dayjs'
import { App, Button, Popconfirm, Space, Tag, Tooltip, Typography } from 'antd'
import { DeleteOutlined, PlusOutlined, ReloadOutlined, StopOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ActionType, ProColumns, ProFormInstance } from '@ant-design/pro-components'

import { listTasksApiTasksGet } from '@/api'
import type { ListTasksApiTasksGetData, TaskKind, TaskResponse, TaskStatus } from '@/api'
import {
  useAccounts,
  useCancelTask,
  useDeleteAllTasks,
  useDeleteTask,
  useProfiles,
  useRetryTask,
} from '@/hooks'
import { handleApiError } from '@/utils/error'

type TaskRow = TaskResponse

type QuickFilterKey =
  | 'all'
  | 'failed'
  | 'waitingCompose'
  | 'waitingUpload'
  | 'scheduled'
  | 'recentlyPublished'

type QueryShape = NonNullable<ListTasksApiTasksGetData['query']>

type TaskListFormValues = {
  status?: TaskStatus
  task_kind?: TaskKind
  account_id?: number
  profile_id?: number
  creative_item_id?: number
  creative_version_id?: number
  batch_id?: string
  failed_at_status?: string
  retry_count_min?: number
  retry_count_max?: number
  created_from?: Dayjs | string
  created_to?: Dayjs | string
  updated_from?: Dayjs | string
  updated_to?: Dayjs | string
  scheduled_from?: Dayjs | string
  scheduled_to?: Dayjs | string
  publish_from?: Dayjs | string
  publish_to?: Dayjs | string
  has_error?: boolean
  has_final_video?: boolean
  current?: number
  pageSize?: number
}

const statusMeta: Record<TaskStatus, { color: string; text: string }> = {
  draft: { color: 'default', text: '待合成' },
  composing: { color: 'processing', text: '合成中' },
  ready: { color: 'warning', text: '待上传' },
  uploading: { color: 'processing', text: '上传中' },
  uploaded: { color: 'success', text: '已上传' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
}

const taskKindMeta: Record<TaskKind, { color: string; text: string }> = {
  composition: { color: 'purple', text: '合成任务' },
  publish: { color: 'blue', text: '发布任务' },
}

const statusValueEnum = Object.fromEntries(
  Object.entries(statusMeta).map(([key, value]) => [key, { text: value.text }]),
)

const taskKindValueEnum = Object.fromEntries(
  Object.entries(taskKindMeta).map(([key, value]) => [key, { text: value.text }]),
)

const booleanOptions = [
  { label: '是', value: true },
  { label: '否', value: false },
]

const terminalStates: ReadonlySet<TaskStatus> = new Set<TaskStatus>(['uploaded', 'cancelled'])

const presetControlledQueryKeys: Array<keyof QueryShape> = [
  'status',
  'task_kind',
  'scheduled_from',
  'scheduled_to',
  'publish_from',
  'publish_to',
]

const hasValue = (value: unknown): boolean => value !== undefined && value !== null && value !== ''

const parseNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }
  return undefined
}

const parseBoolean = (value: unknown): boolean | undefined => {
  if (typeof value === 'boolean') return value
  if (value === 'true') return true
  if (value === 'false') return false
  return undefined
}

const serializeDateTime = (value: unknown): string | undefined => {
  if (dayjs.isDayjs(value)) return value.toISOString()
  if (value instanceof Date) return value.toISOString()
  if (typeof value === 'string' && value) return value
  return undefined
}

const buildTaskListQuery = (params: TaskListFormValues): QueryShape => {
  const query: QueryShape = {}

  if (params.status) query.status = params.status
  if (params.task_kind) query.task_kind = params.task_kind

  const accountId = parseNumber(params.account_id)
  if (accountId !== undefined) query.account_id = accountId

  const profileId = parseNumber(params.profile_id)
  if (profileId !== undefined) query.profile_id = profileId

  const creativeItemId = parseNumber(params.creative_item_id)
  if (creativeItemId !== undefined) query.creative_item_id = creativeItemId

  const creativeVersionId = parseNumber(params.creative_version_id)
  if (creativeVersionId !== undefined) query.creative_version_id = creativeVersionId

  if (typeof params.batch_id === 'string' && params.batch_id.trim()) query.batch_id = params.batch_id.trim()
  if (typeof params.failed_at_status === 'string' && params.failed_at_status.trim()) query.failed_at_status = params.failed_at_status.trim()

  const retryCountMin = parseNumber(params.retry_count_min)
  if (retryCountMin !== undefined) query.retry_count_min = retryCountMin

  const retryCountMax = parseNumber(params.retry_count_max)
  if (retryCountMax !== undefined) query.retry_count_max = retryCountMax

  const createdFrom = serializeDateTime(params.created_from)
  if (createdFrom) query.created_from = createdFrom

  const createdTo = serializeDateTime(params.created_to)
  if (createdTo) query.created_to = createdTo

  const updatedFrom = serializeDateTime(params.updated_from)
  if (updatedFrom) query.updated_from = updatedFrom

  const updatedTo = serializeDateTime(params.updated_to)
  if (updatedTo) query.updated_to = updatedTo

  const scheduledFrom = serializeDateTime(params.scheduled_from)
  if (scheduledFrom) query.scheduled_from = scheduledFrom

  const scheduledTo = serializeDateTime(params.scheduled_to)
  if (scheduledTo) query.scheduled_to = scheduledTo

  const publishFrom = serializeDateTime(params.publish_from)
  if (publishFrom) query.publish_from = publishFrom

  const publishTo = serializeDateTime(params.publish_to)
  if (publishTo) query.publish_to = publishTo

  const hasError = parseBoolean(params.has_error)
  if (hasError !== undefined) query.has_error = hasError

  const hasFinalVideo = parseBoolean(params.has_final_video)
  if (hasFinalVideo !== undefined) query.has_final_video = hasFinalVideo

  if (params.current) query.offset = (params.current - 1) * (params.pageSize ?? 20)
  if (params.pageSize) query.limit = params.pageSize

  return query
}

const getPresetQuery = (key: QuickFilterKey): Partial<QueryShape> => {
  switch (key) {
    case 'failed':
      return { status: 'failed' }
    case 'waitingCompose':
      return { status: 'draft' }
    case 'waitingUpload':
      return { status: 'ready' }
    case 'scheduled':
      return {
        scheduled_from: dayjs().startOf('day').toISOString(),
      }
    case 'recentlyPublished':
      return {
        status: 'uploaded',
        publish_from: dayjs().subtract(7, 'day').startOf('day').toISOString(),
      }
    case 'all':
    default:
      return {}
  }
}

const getPresetFormValues = (key: QuickFilterKey): Partial<TaskListFormValues> => {
  switch (key) {
    case 'failed':
      return { status: 'failed' }
    case 'waitingCompose':
      return { status: 'draft' }
    case 'waitingUpload':
      return { status: 'ready' }
    case 'scheduled':
      return { scheduled_from: dayjs().startOf('day') }
    case 'recentlyPublished':
      return {
        status: 'uploaded',
        publish_from: dayjs().subtract(7, 'day').startOf('day'),
      }
    case 'all':
    default:
      return {}
  }
}

const isPresetActive = (snapshot: Partial<QueryShape>, key: QuickFilterKey): boolean => {
  const expected = getPresetQuery(key)

  if (key === 'all') {
    return presetControlledQueryKeys.every((field) => !hasValue(snapshot[field]))
  }

  return presetControlledQueryKeys.every((field) => {
    const actual = snapshot[field]
    const expectedValue = expected[field]
    if (!hasValue(expectedValue)) return !hasValue(actual)
    return actual === expectedValue
  })
}

const formatDateTime = (value?: string | null): string => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

const quickFilters: Array<{ key: QuickFilterKey; label: string }> = [
  { key: 'all', label: '全部' },
  { key: 'failed', label: '失败任务' },
  { key: 'waitingCompose', label: '待合成' },
  { key: 'waitingUpload', label: '待上传' },
  { key: 'scheduled', label: '计划发布' },
  { key: 'recentlyPublished', label: '最近已发布' },
]

export default function TaskList() {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const actionRef = useRef<ActionType>()
  const formRef = useRef<ProFormInstance<TaskListFormValues>>()
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [searchSnapshot, setSearchSnapshot] = useState<Partial<QueryShape>>({})

  const { data: accounts = [] } = useAccounts()
  const { data: profilesData } = useProfiles()
  const profiles = profilesData?.items ?? []
  const deleteTask = useDeleteTask()
  const deleteAllTasks = useDeleteAllTasks()
  const retryTask = useRetryTask()
  const cancelTask = useCancelTask()

  const accountValueEnum = useMemo(
    () => Object.fromEntries(accounts.map((account) => [account.id, { text: account.account_name }])),
    [accounts],
  )

  const profileValueEnum = useMemo(
    () => Object.fromEntries(profiles.map((profile) => [profile.id, { text: profile.name }])),
    [profiles],
  )

  const syncSearchSnapshot = useCallback((next: Partial<QueryShape>) => {
    setSearchSnapshot((prev) => {
      const prevKeys = Object.keys(prev)
      const nextKeys = Object.keys(next)
      if (prevKeys.length === nextKeys.length && prevKeys.every((key) => prev[key as keyof QueryShape] === next[key as keyof QueryShape])) {
        return prev
      }
      return next
    })
  }, [])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTask.mutateAsync(id)
      message.success('已删除任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除任务失败')
    }
  }, [deleteTask, message])

  const handleRetry = useCallback(async (id: number) => {
    try {
      await retryTask.mutateAsync(id)
      message.success('已发起快速重试')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '快速重试失败')
    }
  }, [message, retryTask])

  const handleCancel = useCallback(async (id: number) => {
    try {
      await cancelTask.mutateAsync(id)
      message.success('已取消任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '取消任务失败')
    }
  }, [cancelTask, message])

  const handleBatchDelete = useCallback(async () => {
    try {
      for (const id of selectedIds) {
        await deleteTask.mutateAsync(id)
      }
      setSelectedIds([])
      message.success(`已删除 ${selectedIds.length} 个任务`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除任务失败')
    }
  }, [deleteTask, message, selectedIds])

  const handleClearAll = useCallback(async () => {
    try {
      await deleteAllTasks.mutateAsync()
      message.success('已清空全部任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '清空任务失败')
    }
  }, [deleteAllTasks, message])

  const handleQuickFilter = useCallback((key: QuickFilterKey) => {
    const currentValues = (formRef.current?.getFieldsValue?.() ?? {}) as TaskListFormValues
    const clearedPresetValues = Object.fromEntries(
      presetControlledQueryKeys.map((field) => [field, undefined]),
    ) as Partial<TaskListFormValues>

    formRef.current?.setFieldsValue({
      ...currentValues,
      ...clearedPresetValues,
      ...getPresetFormValues(key),
    })
    formRef.current?.submit?.()
  }, [])

  const columns: ProColumns<TaskRow>[] = [
    {
      title: '状态',
      dataIndex: 'status',
      width: 110,
      valueType: 'select',
      valueEnum: statusValueEnum,
      fieldProps: { placeholder: '筛选状态', allowClear: true },
      render: (_, record) => {
        const meta = statusMeta[record.status] ?? { color: 'default', text: record.status }
        const tag = <Tag color={meta.color}>{meta.text}</Tag>
        return record.status === 'failed' && record.error_msg ? <Tooltip title={record.error_msg}>{tag}</Tooltip> : tag
      },
    },
    {
      title: '任务',
      key: 'task_identity',
      width: 220,
      hideInSearch: true,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{record.name || `任务 #${record.id}`}</Typography.Text>
          <Typography.Text type="secondary">#{record.id}</Typography.Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'task_kind',
      width: 120,
      valueType: 'select',
      valueEnum: taskKindValueEnum,
      fieldProps: { placeholder: '筛选类型', allowClear: true },
      render: (_, record) => {
        if (!record.task_kind) return <Tag>未标记</Tag>
        const meta = taskKindMeta[record.task_kind]
        return <Tag color={meta.color}>{meta.text}</Tag>
      },
    },
    {
      title: '账号',
      dataIndex: 'account_id',
      width: 180,
      valueType: 'select',
      valueEnum: accountValueEnum,
      fieldProps: { placeholder: '筛选账号', allowClear: true },
      render: (_, record) => (
        record.account_id == null
          ? <Tag>随机分配</Tag>
          : accountValueEnum[record.account_id]?.text ?? `#${record.account_id}`
      ),
    },
    {
      title: '配置档',
      dataIndex: 'profile_id',
      width: 180,
      valueType: 'select',
      valueEnum: profileValueEnum,
      fieldProps: { placeholder: '筛选配置档', allowClear: true },
      render: (_, record) => (
        record.profile_id == null
          ? <Typography.Text type="secondary">默认/未指定</Typography.Text>
          : profileValueEnum[record.profile_id]?.text ?? `#${record.profile_id}`
      ),
    },
    {
      title: '作品链路',
      key: 'creative_lineage',
      width: 180,
      hideInSearch: true,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>{record.creative_item_id ? `作品 #${record.creative_item_id}` : '作品 -'}</Typography.Text>
          <Typography.Text type="secondary">{record.creative_version_id ? `版本 #${record.creative_version_id}` : '版本 -'}</Typography.Text>
        </Space>
      ),
    },
    {
      title: '批次',
      dataIndex: 'batch_id',
      width: 180,
      ellipsis: true,
      fieldProps: { placeholder: '按批次筛选', allowClear: true },
      render: (_, record) => record.batch_id ?? '-',
    },
    {
      title: '计划发布时间',
      dataIndex: 'scheduled_time',
      width: 180,
      hideInSearch: true,
      render: (_, record) => formatDateTime(record.scheduled_time),
    },
    {
      title: '实际发布时间',
      dataIndex: 'publish_time',
      width: 180,
      hideInSearch: true,
      render: (_, record) => formatDateTime(record.publish_time),
    },
    {
      title: '重试/失败阶段',
      key: 'retry_state',
      width: 180,
      hideInSearch: true,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>重试 {record.retry_count ?? 0}</Typography.Text>
          <Typography.Text type="secondary">{record.failed_at_status ? `失败于 ${record.failed_at_status}` : '失败阶段 -'}</Typography.Text>
        </Space>
      ),
    },
    {
      title: '最近更新',
      dataIndex: 'updated_at',
      width: 180,
      hideInSearch: true,
      render: (_, record) => formatDateTime(record.updated_at),
    },
    {
      title: '作品 ID',
      dataIndex: 'creative_item_id',
      hideInTable: true,
      valueType: 'digit',
      fieldProps: { placeholder: '按作品 ID 筛选' },
    },
    {
      title: '版本 ID',
      dataIndex: 'creative_version_id',
      hideInTable: true,
      valueType: 'digit',
      fieldProps: { placeholder: '按版本 ID 筛选' },
    },
    {
      title: '失败阶段',
      dataIndex: 'failed_at_status',
      hideInTable: true,
      fieldProps: { placeholder: '例如 uploading / composing' },
    },
    {
      title: '最少重试次数',
      dataIndex: 'retry_count_min',
      hideInTable: true,
      valueType: 'digit',
      fieldProps: { placeholder: '最少重试次数' },
    },
    {
      title: '最多重试次数',
      dataIndex: 'retry_count_max',
      hideInTable: true,
      valueType: 'digit',
      fieldProps: { placeholder: '最多重试次数' },
    },
    {
      title: '创建起始',
      dataIndex: 'created_from',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '创建截止',
      dataIndex: 'created_to',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '更新起始',
      dataIndex: 'updated_from',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '更新截止',
      dataIndex: 'updated_to',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '计划发布起始',
      dataIndex: 'scheduled_from',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '计划发布截止',
      dataIndex: 'scheduled_to',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '实际发布起始',
      dataIndex: 'publish_from',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '实际发布截止',
      dataIndex: 'publish_to',
      hideInTable: true,
      valueType: 'dateTime',
    },
    {
      title: '有错误信息',
      dataIndex: 'has_error',
      hideInTable: true,
      valueType: 'select',
      fieldProps: { options: booleanOptions, placeholder: '是否已有错误信息', allowClear: true },
    },
    {
      title: '有最终视频',
      dataIndex: 'has_final_video',
      hideInTable: true,
      valueType: 'select',
      fieldProps: { options: booleanOptions, placeholder: '是否已有最终视频', allowClear: true },
    },
    {
      title: '操作',
      key: 'action',
      width: 220,
      hideInSearch: true,
      render: (_, record) => {
        const canRetry = record.status === 'failed'
        const canCancel = !terminalStates.has(record.status) && record.status !== 'failed'

        return (
          <Space size={4}>
            <Button
              type="link"
              size="small"
              onClick={(event) => {
                event.stopPropagation()
                navigate(`/task/${record.id}`)
              }}
            >
              查看详情
            </Button>
            {canRetry ? (
              <Button
                type="link"
                size="small"
                icon={<ReloadOutlined />}
                onClick={(event) => {
                  event.stopPropagation()
                  void handleRetry(record.id)
                }}
              >
                重试
              </Button>
            ) : null}
            {canCancel ? (
              <Popconfirm
                title="确认取消这个任务吗？"
                onConfirm={(event) => {
                  event?.stopPropagation()
                  void handleCancel(record.id)
                }}
              >
                <Button
                  type="link"
                  size="small"
                  icon={<StopOutlined />}
                  onClick={(event) => event.stopPropagation()}
                >
                  取消
                </Button>
              </Popconfirm>
            ) : null}
            <Popconfirm
              title="确认删除这个任务吗？"
              onConfirm={(event) => {
                event?.stopPropagation()
                void handleDelete(record.id)
              }}
            >
              <Button
                type="link"
                danger
                size="small"
                icon={<DeleteOutlined />}
                onClick={(event) => event.stopPropagation()}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        )
      },
    },
  ]

  return (
    <ProTable<TaskRow, TaskListFormValues>
      actionRef={actionRef}
      formRef={formRef}
      rowKey="id"
      columns={columns}
      headerTitle={<span data-testid="task-list-semantics">任务管理</span>}
      request={async (params) => {
        const query = buildTaskListQuery(params)
        const { limit, offset, ...searchOnlyQuery } = query
        syncSearchSnapshot(searchOnlyQuery)
        const response = await listTasksApiTasksGet({ query })
        const data = response.data ?? { total: 0, items: [] }
        return { data: data.items as TaskRow[], success: true, total: data.total }
      }}
      tableExtraRender={() => (
        <Space wrap>
          <Typography.Text type="secondary">快捷筛选：</Typography.Text>
          {quickFilters.map((filter) => (
            <Button
              key={filter.key}
              size="small"
              type={isPresetActive(searchSnapshot, filter.key) ? 'primary' : 'default'}
              onClick={() => handleQuickFilter(filter.key)}
            >
              {filter.label}
            </Button>
          ))}
        </Space>
      )}
      rowSelection={{
        selectedRowKeys: selectedIds,
        onChange: (keys) => setSelectedIds(keys as number[]),
      }}
      tableAlertOptionRender={() => (
        <Popconfirm title={`确认删除已选中的 ${selectedIds.length} 个任务吗？`} onConfirm={() => void handleBatchDelete()}>
          <Button danger size="small" icon={<DeleteOutlined />} loading={deleteTask.isPending}>
            删除已选 {selectedIds.length} 项
          </Button>
        </Popconfirm>
      )}
      toolBarRender={() => [
        <Button
          key="workbench"
          onClick={() => navigate('/creative/workbench')}
          data-testid="task-list-open-workbench"
        >
          返回作品工作台
        </Button>,
        <Button key="create" type="primary" icon={<PlusOutlined />} onClick={() => navigate('/task/create')}>
          新建任务
        </Button>,
        <Popconfirm key="clear" title="确认清空全部任务吗？" onConfirm={() => void handleClearAll()}>
          <Button danger loading={deleteAllTasks.isPending}>清空全部任务</Button>
        </Popconfirm>,
      ]}
      onRow={(record) => ({
        onClick: () => navigate(`/task/${record.id}`),
        style: { cursor: 'pointer' },
      })}
      pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
      search={{
        labelWidth: 'auto',
        defaultCollapsed: false,
        span: 6,
      }}
      size="small"
    />
  )
}
