import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Popconfirm, Space, Tag, Tooltip, message } from 'antd'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ActionType, ProColumns } from '@ant-design/pro-components'

import { listTasksApiTasksGet } from '@/api'
import type { TaskResponse } from '@/api'
import { useAccounts, useDeleteAllTasks, useDeleteTask } from '@/hooks'
import { handleApiError } from '@/utils/error'

type TaskStatus = 'draft' | 'composing' | 'ready' | 'uploading' | 'uploaded' | 'failed' | 'cancelled'

type TaskRow = TaskResponse

const statusMap: Record<TaskStatus, { color: string; text: string }> = {
  draft: { color: 'default', text: 'Draft' },
  composing: { color: 'processing', text: 'Composing' },
  ready: { color: 'warning', text: 'Ready' },
  uploading: { color: 'processing', text: 'Uploading' },
  uploaded: { color: 'success', text: 'Uploaded' },
  failed: { color: 'error', text: 'Failed' },
  cancelled: { color: 'default', text: 'Cancelled' },
}

const statusValueEnum = Object.fromEntries(
  Object.entries(statusMap).map(([key, value]) => [key, { text: value.text }]),
)

export default function TaskList() {
  const navigate = useNavigate()
  const actionRef = useRef<ActionType>()
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const { data: accounts = [] } = useAccounts()
  const deleteTask = useDeleteTask()
  const deleteAllTasks = useDeleteAllTasks()

  const accountValueEnum = Object.fromEntries(
    accounts.map((account) => [account.id, { text: account.account_name }]),
  )

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTask.mutateAsync(id)
      message.success('Task deleted')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, 'Delete failed')
    }
  }, [deleteTask])

  const handleBatchDelete = useCallback(async () => {
    try {
      for (const id of selectedIds) {
        await deleteTask.mutateAsync(id)
      }
      setSelectedIds([])
      message.success(`Deleted ${selectedIds.length} tasks`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, 'Batch delete failed')
    }
  }, [deleteTask, selectedIds])

  const handleClearAll = useCallback(async () => {
    try {
      await deleteAllTasks.mutateAsync()
      message.success('All tasks cleared')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, 'Clear failed')
    }
  }, [deleteAllTasks])

  const columns: ProColumns<TaskRow>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 70,
      sorter: true,
      hideInSearch: true,
    },
    {
      title: 'Task name',
      dataIndex: 'name',
      ellipsis: true,
      hideInSearch: true,
      render: (_, record) => record.name || `Task #${record.id}`,
    },
    {
      title: 'Account',
      dataIndex: 'account_id',
      width: 130,
      valueType: 'select',
      valueEnum: accountValueEnum,
      fieldProps: { placeholder: 'Filter by account', allowClear: true },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      width: 100,
      valueType: 'select',
      valueEnum: statusValueEnum,
      fieldProps: { placeholder: 'Filter by status', allowClear: true },
      render: (_, record) => {
        const { color, text } = statusMap[record.status] ?? { color: 'default', text: record.status }
        const tag = <Tag color={color}>{text}</Tag>
        if (record.status === 'failed' && record.error_msg) {
          return <Tooltip title={record.error_msg}>{tag}</Tooltip>
        }
        return tag
      },
    },
    {
      title: 'Materials',
      key: 'materials',
      width: 180,
      hideInSearch: true,
      render: (_, record) => {
        const parts: string[] = []
        if ((record.video_ids?.length ?? 0) > 0) parts.push(`${record.video_ids?.length ?? 0} videos`)
        if ((record.copywriting_ids?.length ?? 0) > 0) parts.push(`${record.copywriting_ids?.length ?? 0} copy`)
        if ((record.cover_ids?.length ?? 0) > 0) parts.push(`${record.cover_ids?.length ?? 0} covers`)
        if ((record.audio_ids?.length ?? 0) > 0) parts.push(`${record.audio_ids?.length ?? 0} audio`)
        return parts.length ? parts.join(' / ') : '-'
      },
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      width: 80,
      hideInSearch: true,
      sorter: true,
    },
    {
      title: 'Created at',
      dataIndex: 'created_at',
      width: 160,
      sorter: true,
      hideInSearch: true,
      render: (_, record) => new Date(record.created_at).toLocaleString('zh-CN'),
    },
    {
      title: 'Action',
      key: 'action',
      width: 90,
      hideInSearch: true,
      render: (_, record) => (
        <Popconfirm title="Delete this task?" onConfirm={(event) => { event?.stopPropagation(); void handleDelete(record.id) }}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />} onClick={(event) => event.stopPropagation()}>
            Delete
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Alert
        type="info"
        showIcon
        data-testid="task-list-semantics"
        message="Execution / diagnostics tasks"
        description="Use this list for execution, retries, and troubleshooting. Creative workbench and Creative detail stay the primary business surfaces."
      />

      <ProTable<TaskRow>
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        headerTitle="Execution / diagnostics"
        request={async (params) => {
          const query: Record<string, string | number> = {}
          if (params.status) query.status = params.status
          if (params.account_id) query.account_id = params.account_id
          if (params.current) query.offset = (params.current - 1) * (params.pageSize ?? 20)
          if (params.pageSize) query.limit = params.pageSize

          const response = await listTasksApiTasksGet({ query })
          const data = response.data ?? { total: 0, items: [] }
          return { data: data.items as TaskRow[], success: true, total: data.total }
        }}
        rowSelection={{
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        }}
        tableAlertOptionRender={() => (
          <Popconfirm title={`Delete ${selectedIds.length} selected tasks?`} onConfirm={() => void handleBatchDelete()}>
            <Button danger size="small" icon={<DeleteOutlined />} loading={deleteTask.isPending}>
              Batch delete ({selectedIds.length})
            </Button>
          </Popconfirm>
        )}
        toolBarRender={() => [
          <Button key="workbench" onClick={() => navigate('/creative/workbench')} data-testid="task-list-open-workbench">
            Back to creative workbench
          </Button>,
          <Button key="create" type="primary" icon={<PlusOutlined />} onClick={() => navigate('/task/create')}>
            Create execution task
          </Button>,
          <Popconfirm key="clear" title="Clear all tasks?" onConfirm={() => void handleClearAll()}>
            <Button danger loading={deleteAllTasks.isPending}>Clear all tasks</Button>
          </Popconfirm>,
        ]}
        onRow={(record) => ({
          onClick: () => navigate(`/task/${record.id}`),
          style: { cursor: 'pointer' },
        })}
        pagination={{ pageSize: 20, showTotal: (total) => `${total} tasks` }}
        size="small"
        search={{ labelWidth: 'auto' }}
      />
    </Space>
  )
}
