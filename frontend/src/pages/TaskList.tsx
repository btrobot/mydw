import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Popconfirm, Tag, Tooltip, message } from 'antd'
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
  draft: { color: 'default', text: '草稿' },
  composing: { color: 'processing', text: '合成中' },
  ready: { color: 'warning', text: '待上传' },
  uploading: { color: 'processing', text: '上传中' },
  uploaded: { color: 'success', text: '已上传' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
}

const statusValueEnum = Object.fromEntries(Object.entries(statusMap).map(([key, value]) => [key, { text: value.text }]))

export default function TaskList() {
  const navigate = useNavigate()
  const actionRef = useRef<ActionType>()
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const { data: accounts = [] } = useAccounts()
  const deleteTask = useDeleteTask()
  const deleteAllTasks = useDeleteAllTasks()

  const accountValueEnum = Object.fromEntries(accounts.map((account) => [account.id, { text: account.account_name }]))

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTask.mutateAsync(id)
      message.success('已删除任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除任务失败')
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
      handleApiError(error, '批量删除任务失败')
    }
  }, [deleteTask, selectedIds])

  const handleClearAll = useCallback(async () => {
    try {
      await deleteAllTasks.mutateAsync()
      message.success('已清空全部任务')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '清空任务失败')
    }
  }, [deleteAllTasks])

  const columns: ProColumns<TaskRow>[] = [
    { title: 'ID', dataIndex: 'id', width: 70, sorter: true, hideInSearch: true },
    { title: '任务名称', dataIndex: 'name', ellipsis: true, hideInSearch: true, render: (_, record) => record.name || `任务 #${record.id}` },
    { title: '账号', dataIndex: 'account_id', width: 130, valueType: 'select', valueEnum: accountValueEnum, fieldProps: { placeholder: '筛选账号', allowClear: true } },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      valueType: 'select',
      valueEnum: statusValueEnum,
      fieldProps: { placeholder: '筛选状态', allowClear: true },
      render: (_, record) => {
        const { color, text } = statusMap[record.status] ?? { color: 'default', text: record.status }
        const tag = <Tag color={color}>{text}</Tag>
        return record.status === 'failed' && record.error_msg ? <Tooltip title={record.error_msg}>{tag}</Tooltip> : tag
      },
    },
    {
      title: '素材',
      key: 'materials',
      width: 180,
      hideInSearch: true,
      render: (_, record) => {
        const parts: string[] = []
        if ((record.video_ids?.length ?? 0) > 0) parts.push(`${record.video_ids?.length ?? 0} 个视频`)
        if ((record.copywriting_ids?.length ?? 0) > 0) parts.push(`${record.copywriting_ids?.length ?? 0} 条文案`)
        if ((record.cover_ids?.length ?? 0) > 0) parts.push(`${record.cover_ids?.length ?? 0} 张封面`)
        if ((record.audio_ids?.length ?? 0) > 0) parts.push(`${record.audio_ids?.length ?? 0} 条音频`)
        return parts.length ? parts.join(' / ') : '-'
      },
    },
    { title: '优先级', dataIndex: 'priority', width: 80, hideInSearch: true, sorter: true },
    { title: '创建时间', dataIndex: 'created_at', width: 160, sorter: true, hideInSearch: true, render: (_, record) => new Date(record.created_at).toLocaleString('zh-CN') },
    {
      title: '操作',
      key: 'action',
      width: 90,
      hideInSearch: true,
      render: (_, record) => (
        <Popconfirm title="确认删除这个任务吗？" onConfirm={(event) => { event?.stopPropagation(); void handleDelete(record.id) }}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />} onClick={(event) => event.stopPropagation()}>删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <Alert type="info" showIcon data-testid="task-list-semantics" message="执行与诊断任务列表" description="这里用于查看任务执行、重试与排障链路；作品业务主路径仍在作品工作台与作品详情。" />

      <ProTable<TaskRow>
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        headerTitle="任务诊断列表"
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
        rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
        tableAlertOptionRender={() => (
          <Popconfirm title={`确认删除已选中的 ${selectedIds.length} 个任务吗？`} onConfirm={() => void handleBatchDelete()}>
            <Button danger size="small" icon={<DeleteOutlined />} loading={deleteTask.isPending}>删除已选 {selectedIds.length} 项</Button>
          </Popconfirm>
        )}
        toolBarRender={() => [
          <Button key="workbench" onClick={() => navigate('/creative/workbench')} data-testid="task-list-open-workbench">返回作品工作台</Button>,
          <Button key="create" type="primary" icon={<PlusOutlined />} onClick={() => navigate('/task/create')}>新建任务</Button>,
          <Popconfirm key="clear" title="确认清空全部任务吗？" onConfirm={() => void handleClearAll()}><Button danger loading={deleteAllTasks.isPending}>清空全部任务</Button></Popconfirm>,
        ]}
        onRow={(record) => ({ onClick: () => navigate(`/task/${record.id}`), style: { cursor: 'pointer' } })}
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
        size="small"
        search={{ labelWidth: 'auto' }}
      />
    </>
  )
}
