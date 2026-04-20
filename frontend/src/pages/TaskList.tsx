import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import dayjs, { type Dayjs } from 'dayjs'
import { App, Button, Input, Popconfirm, Space, Tag, Tooltip, Typography } from 'antd'
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

import { getTaskActionAvailability, taskKindMeta, taskStatusMeta } from './task/taskPresentation'

type TaskRow = TaskResponse
type QueryShape = NonNullable<ListTasksApiTasksGetData['query']>
type DateRangeValue = [Dayjs, Dayjs]

type QuickFilterKey =
  | 'all'
  | 'failed'
  | 'waitingCompose'
  | 'waitingUpload'
  | 'scheduled'
  | 'recentlyPublished'

type TaskListFormValues = {
  name?: string
  status?: TaskStatus
  task_kind?: TaskKind
  account_id?: number
  profile_id?: number
  failed_at_status?: string
  updated_range?: DateRangeValue
  scheduled_from?: Dayjs | string
  scheduled_to?: Dayjs | string
  publish_from?: Dayjs | string
  publish_to?: Dayjs | string
  current?: number
  pageSize?: number
}

const statusValueEnum = Object.fromEntries(
  Object.entries(taskStatusMeta).map(([key, value]) => [key, { text: value.text }]),
)

const taskKindValueEnum = Object.fromEntries(
  Object.entries(taskKindMeta).map(([key, value]) => [key, { text: value.text }]),
)

const presetControlledQueryKeys: Array<keyof QueryShape> = [
  'status',
  'task_kind',
  'scheduled_from',
  'scheduled_to',
  'publish_from',
  'publish_to',
]

const stringFieldKeys = ['name', 'status', 'task_kind', 'failed_at_status'] as const
const numberFieldKeys = ['account_id', 'profile_id'] as const
const hiddenPresetDateFieldKeys = ['scheduled_from', 'scheduled_to', 'publish_from', 'publish_to'] as const

const hasValue = (value: unknown): boolean => value !== undefined && value !== null && value !== ''

const parseNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }
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

  if (typeof params.name === 'string' && params.name.trim()) query.name = params.name.trim()
  if (params.status) query.status = params.status
  if (params.task_kind) query.task_kind = params.task_kind

  const accountId = parseNumber(params.account_id)
  if (accountId !== undefined) query.account_id = accountId

  const profileId = parseNumber(params.profile_id)
  if (profileId !== undefined) query.profile_id = profileId

  if (
    params.status === 'failed'
    && typeof params.failed_at_status === 'string'
    && params.failed_at_status.trim()
  ) {
    query.failed_at_status = params.failed_at_status.trim()
  }

  if (params.updated_range?.length === 2) {
    const [updatedFrom, updatedTo] = params.updated_range
    query.updated_from = updatedFrom.toISOString()
    query.updated_to = updatedTo.toISOString()
  }

  const scheduledFrom = serializeDateTime(params.scheduled_from)
  if (scheduledFrom) query.scheduled_from = scheduledFrom

  const scheduledTo = serializeDateTime(params.scheduled_to)
  if (scheduledTo) query.scheduled_to = scheduledTo

  const publishFrom = serializeDateTime(params.publish_from)
  if (publishFrom) query.publish_from = publishFrom

  const publishTo = serializeDateTime(params.publish_to)
  if (publishTo) query.publish_to = publishTo

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

const getErrorDetail = (error: unknown): string | undefined => {
  if (
    error !== null
    && typeof error === 'object'
    && 'detail' in error
    && typeof (error as { detail?: unknown }).detail === 'string'
  ) {
    return (error as { detail: string }).detail
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return undefined
}

const buildTaskListSearchParams = (
  query: QueryShape,
  pagination: { current?: number; pageSize?: number },
): URLSearchParams => {
  const nextSearchParams = new URLSearchParams()

  for (const [key, value] of Object.entries(query)) {
    if (key === 'offset' || key === 'limit' || !hasValue(value)) continue
    nextSearchParams.set(key, String(value))
  }

  const pageSize = query.limit ?? pagination.pageSize ?? 20
  const current = query.offset !== undefined ? Math.floor(query.offset / pageSize) + 1 : (pagination.current ?? 1)

  nextSearchParams.set('page', String(current))
  nextSearchParams.set('pageSize', String(pageSize))

  return nextSearchParams
}

const parseTaskListStateFromSearchParams = (searchParams: URLSearchParams) => {
  const formValues: TaskListFormValues = {}
  const searchSnapshot: Partial<QueryShape> = {}

  for (const key of stringFieldKeys) {
    const value = searchParams.get(key)
    if (!value) continue
    ;(formValues as Record<string, unknown>)[key] = value
    ;(searchSnapshot as Record<string, unknown>)[key] = value
  }

  for (const key of numberFieldKeys) {
    const value = parseNumber(searchParams.get(key))
    if (value === undefined) continue
    ;(formValues as Record<string, unknown>)[key] = value
    ;(searchSnapshot as Record<string, unknown>)[key] = value
  }

  for (const key of hiddenPresetDateFieldKeys) {
    const value = searchParams.get(key)
    if (!value) continue
    const parsed = dayjs(value)
    ;(formValues as Record<string, unknown>)[key] = parsed.isValid() ? parsed : value
    ;(searchSnapshot as Record<string, unknown>)[key] = value
  }

  const updatedFrom = searchParams.get('updated_from')
  const updatedTo = searchParams.get('updated_to')
  if (updatedFrom) searchSnapshot.updated_from = updatedFrom
  if (updatedTo) searchSnapshot.updated_to = updatedTo
  if (updatedFrom && updatedTo) {
    const parsedFrom = dayjs(updatedFrom)
    const parsedTo = dayjs(updatedTo)
    if (parsedFrom.isValid() && parsedTo.isValid()) {
      formValues.updated_range = [parsedFrom, parsedTo]
    }
  }

  const current = parseNumber(searchParams.get('page')) ?? 1
  const pageSize = parseNumber(searchParams.get('pageSize')) ?? 20

  formValues.current = current
  formValues.pageSize = pageSize

  return {
    formValues,
    searchSnapshot,
    current,
    pageSize,
  }
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
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const { message } = App.useApp()
  const actionRef = useRef<ActionType>()
  const formRef = useRef<ProFormInstance<TaskListFormValues>>()
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const initialRouteState = useMemo(
    () => parseTaskListStateFromSearchParams(searchParams),
    [searchParams],
  )
  const [searchSnapshot, setSearchSnapshot] = useState<Partial<QueryShape>>(
    initialRouteState.searchSnapshot,
  )

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

  const getCurrentReturnTo = useCallback(() => {
    const currentPath = `${location.pathname}${location.search}`
    return currentPath || '/task/list'
  }, [location.pathname, location.search])

  const openTaskDetail = useCallback((taskId: number) => {
    const params = new URLSearchParams({ returnTo: getCurrentReturnTo() })
    navigate(`/task/${taskId}?${params.toString()}`)
  }, [getCurrentReturnTo, navigate])

  const syncSearchSnapshot = useCallback((next: Partial<QueryShape>) => {
    setSearchSnapshot((prev) => {
      const prevKeys = Object.keys(prev)
      const nextKeys = Object.keys(next)
      if (
        prevKeys.length === nextKeys.length
        && prevKeys.every((key) => prev[key as keyof QueryShape] === next[key as keyof QueryShape])
      ) {
        return prev
      }
      return next
    })
  }, [])

  useEffect(() => {
    syncSearchSnapshot(initialRouteState.searchSnapshot)
  }, [initialRouteState.searchSnapshot, syncSearchSnapshot])

  const showTaskActionError = useCallback((error: unknown, fallback: string) => {
    const detail = getErrorDetail(error)
    const isDeleteConflict = typeof detail === 'string' && detail.includes('发布规划引用')

    if (isDeleteConflict) {
      message.warning(detail)
      return
    }

    message.error(detail ?? fallback)
  }, [message])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTask.mutateAsync(id)
      message.success('已删除任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      showTaskActionError(error, '删除任务失败')
    }
  }, [deleteTask, message, showTaskActionError])

  const handleRetry = useCallback(async (id: number) => {
    try {
      await retryTask.mutateAsync(id)
      message.success('已发起快速重试')
      actionRef.current?.reload()
    } catch (error: unknown) {
      showTaskActionError(error, '快速重试失败')
    }
  }, [message, retryTask, showTaskActionError])

  const handleCancel = useCallback(async (id: number) => {
    try {
      await cancelTask.mutateAsync(id)
      message.success('已取消任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      showTaskActionError(error, '取消任务失败')
    }
  }, [cancelTask, message, showTaskActionError])

  const handleBatchDelete = useCallback(async () => {
    let deletedCount = 0

    try {
      for (const id of selectedIds) {
        await deleteTask.mutateAsync(id)
        deletedCount += 1
      }
      setSelectedIds([])
      message.success(`已删除 ${selectedIds.length} 个任务`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      if (deletedCount > 0) {
        actionRef.current?.reload()
        const detail = getErrorDetail(error)
        const suffix = detail ? `；${detail}` : ''
        message.warning(`已删除 ${deletedCount} 个任务，剩余任务未删除${suffix}`)
        return
      }

      showTaskActionError(error, '批量删除任务失败')
    }
  }, [deleteTask, message, selectedIds, showTaskActionError])

  const handleClearAll = useCallback(async () => {
    try {
      await deleteAllTasks.mutateAsync()
      message.success('已清空全部任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      showTaskActionError(error, '清空任务失败')
    }
  }, [deleteAllTasks, message, showTaskActionError])

  const handleQuickFilter = useCallback((key: QuickFilterKey) => {
    const currentValues = (formRef.current?.getFieldsValue?.(true) ?? {}) as TaskListFormValues
    const clearedPresetValues = Object.fromEntries(
      presetControlledQueryKeys.map((field) => [field, undefined]),
    ) as Partial<TaskListFormValues>

    formRef.current?.setFieldsValue({
      ...currentValues,
      ...clearedPresetValues,
      failed_at_status: undefined,
      ...getPresetFormValues(key),
    })
    formRef.current?.submit?.()
  }, [])

  const columns: ProColumns<TaskRow>[] = [
    {
      title: '名称',
      dataIndex: 'name',
      hideInTable: true,
      order: 1,
      renderFormItem: () => <Input placeholder="按任务名称搜索" allowClear />,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 110,
      valueType: 'select',
      valueEnum: statusValueEnum,
      order: 4,
      fieldProps: { placeholder: '筛选状态', allowClear: true },
      render: (_, record) => {
        const meta = taskStatusMeta[record.status] ?? { color: 'default', text: record.status }
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
      order: 3,
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
      order: 2,
      fieldProps: { placeholder: '筛选账号', allowClear: true },
      render: (_, record) => (
        record.account_id == null
          ? <Tag>随机分配</Tag>
          : accountValueEnum[record.account_id]?.text ?? `#${record.account_id}`
      ),
    },
    {
      title: '最近更新',
      dataIndex: 'updated_range',
      hideInTable: true,
      valueType: 'dateTimeRange',
      order: 5,
      fieldProps: {
        placeholder: ['开始时间', '结束时间'],
      },
    },
    {
      title: '合成配置',
      dataIndex: 'profile_id',
      width: 180,
      valueType: 'select',
      valueEnum: profileValueEnum,
      order: 6,
      fieldProps: { placeholder: '筛选合成配置', allowClear: true },
      render: (_, record) => (
        record.profile_id == null
          ? <Typography.Text type="secondary">默认/未指定</Typography.Text>
          : profileValueEnum[record.profile_id]?.text ?? `#${record.profile_id}`
      ),
    },
    {
      title: '失败阶段',
      dataIndex: 'failed_at_status',
      hideInTable: true,
      order: 7,
      renderFormItem: () => <Input placeholder="例如 uploading / composing" allowClear />,
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
      hideInSearch: true,
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
      title: '操作',
      key: 'action',
      width: 220,
      hideInSearch: true,
      render: (_, record) => {
        const { canRetry, canCancel } = getTaskActionAvailability(record.status)

        return (
          <Space size={4}>
            <Button
              type="link"
              size="small"
              onClick={(event) => {
                event.stopPropagation()
                openTaskDetail(record.id)
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
        const nextSearchParams = buildTaskListSearchParams(query, {
          current: params.current,
          pageSize: params.pageSize,
        })
        if (nextSearchParams.toString() !== searchParams.toString()) {
          setSearchParams(nextSearchParams, { replace: true })
        }
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
        onClick: () => openTaskDetail(record.id),
        style: { cursor: 'pointer' },
      })}
      pagination={{
        current: initialRouteState.current,
        pageSize: initialRouteState.pageSize,
        showTotal: (total) => `共 ${total} 条`,
      }}
      form={{
        initialValues: initialRouteState.formValues,
      }}
      search={{
        labelWidth: 'auto',
        defaultCollapsed: true,
        span: 6,
      }}
      size="small"
    />
  )
}
