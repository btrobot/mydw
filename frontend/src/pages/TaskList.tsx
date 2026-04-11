import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Tag, Button, Popconfirm, Tooltip, message } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'
import { listTasksApiTasksGet } from '@/api'
import type { TaskResponse } from '@/api'

import { useAccounts, useDeleteTask, useDeleteAllTasks } from '@/hooks'
import { handleApiError } from '@/utils/error'

type TaskStatus = 'draft' | 'composing' | 'ready' | 'uploading' | 'uploaded' | 'failed' | 'cancelled'

type TaskRow = TaskResponse

const statusMap: Record<TaskStatus, { color: string; text: string }> = {
  draft:     { color: 'default',    text: '草稿' },
  composing: { color: 'processing', text: '合成中' },
  ready:     { color: 'warning',    text: '待上传' },
  uploading: { color: 'processing', text: '上传中' },
  uploaded:  { color: 'success',    text: '已上传' },
  failed:    { color: 'error',      text: '失败' },
  cancelled: { color: 'default',    text: '已取消' },
}

const statusValueEnum = Object.fromEntries(
  Object.entries(statusMap).map(([k, v]) => [k, { text: v.text }])
)

export default function TaskList() {
  const navigate = useNavigate()
  const actionRef = useRef<ActionType>()
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const { data: accounts = [] } = useAccounts()
  const deleteTask = useDeleteTask()
  const deleteAllTasks = useDeleteAllTasks()

  const accountValueEnum = Object.fromEntries(
    accounts.map((a) => [a.id, { text: a.account_name }])
  )

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTask.mutateAsync(id)
      message.success('删除成功')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除失败')
    }
  }, [deleteTask])

  const handleBatchDelete = useCallback(async () => {
    try {
      for (const id of selectedIds) {
        await deleteTask.mutateAsync(id)
      }
      setSelectedIds([])
      message.success(`已删除 ${selectedIds.length} 个任务`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, deleteTask])

  const handleClearAll = useCallback(async () => {
    try {
      await deleteAllTasks.mutateAsync()
      message.success('已清空所有任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '清空失败')
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
      title: '任务名称',
      dataIndex: 'name',
      ellipsis: true,
      hideInSearch: true,
      render: (_, record) => record.name || `任务 #${record.id}`,
    },
    {
      title: '账号',
      dataIndex: 'account_id',
      width: 130,
      valueType: 'select',
      valueEnum: accountValueEnum,
      fieldProps: { placeholder: '按账号筛选', allowClear: true },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      valueType: 'select',
      valueEnum: statusValueEnum,
      fieldProps: { placeholder: '按状态筛选', allowClear: true },
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
      title: '素材',
      key: 'materials',
      width: 160,
      hideInSearch: true,
      render: (_, record) => {
        const parts: string[] = []
        if ((record.video_ids?.length ?? 0) > 0) parts.push(`${record.video_ids?.length ?? 0} 视频`)
        if ((record.copywriting_ids?.length ?? 0) > 0) parts.push(`${record.copywriting_ids?.length ?? 0} 文案`)
        if ((record.cover_ids?.length ?? 0) > 0) parts.push(`${record.cover_ids?.length ?? 0} 封面`)
        if ((record.audio_ids?.length ?? 0) > 0) parts.push(`${record.audio_ids?.length ?? 0} 音频`)
        return parts.length ? parts.join(' / ') : '-'
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      width: 80,
      hideInSearch: true,
      sorter: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      sorter: true,
      hideInSearch: true,
      render: (_, record) => new Date(record.created_at).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      hideInSearch: true,
      render: (_, record) => (
        <Popconfirm title="确定删除？" onConfirm={(e) => { e?.stopPropagation(); handleDelete(record.id) }}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />} onClick={(e) => e.stopPropagation()}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <ProTable<TaskRow>
      actionRef={actionRef}
      rowKey="id"
      columns={columns}
      request={async (params) => {
        const query: Record<string, string | number> = {}
        if (params.status) query.status = params.status
        if (params.account_id) query.account_id = params.account_id
        if (params.current) query.offset = ((params.current - 1) * (params.pageSize ?? 20))
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
        <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
          <Button danger size="small" icon={<DeleteOutlined />} loading={deleteTask.isPending}>
            批量删除 ({selectedIds.length})
          </Button>
        </Popconfirm>
      )}
      toolBarRender={() => [
        <Button key="create" type="primary" icon={<PlusOutlined />} onClick={() => navigate('/task/create')}>
          创建任务
        </Button>,
        <Popconfirm key="clear" title="确定清空所有任务？" onConfirm={handleClearAll}>
          <Button danger loading={deleteAllTasks.isPending}>清空所有</Button>
        </Popconfirm>,
      ]}
      onRow={(record) => ({
        onClick: () => navigate(`/task/${record.id}`),
        style: { cursor: 'pointer' },
      })}
      pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
      size="small"
      search={{ labelWidth: 'auto' }}
    />
  )
}
