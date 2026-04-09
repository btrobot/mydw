import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table, Tag, Button, Space, Popconfirm, Row, Col, Tooltip,
} from 'antd'
import {
  ReloadOutlined, AppstoreAddOutlined,
} from '@ant-design/icons'
import {
  useTasks,
  useAccounts,
  useDeleteTask,
  useDeleteAllTasks,
} from '../hooks'
import { useVideos } from '../hooks/useVideo'
import { message } from 'antd'
import type { AccountResponseExtended } from '../hooks/useAccount'
import type { VideoResponse } from '@/types/material'

type TaskStatus =
  | 'draft'
  | 'composing'
  | 'ready'
  | 'uploading'
  | 'uploaded'
  | 'failed'
  | 'cancelled'

interface Task {
  id: number
  account_id: number
  video_id?: number | null
  topic_ids?: number[] | null
  status: TaskStatus
  publish_time?: string | null
  error_msg?: string | null
  priority: number
  created_at: string
}

const statusMap: Record<TaskStatus, { color: string; text: string }> = {
  draft:      { color: 'default',    text: '草稿' },
  composing:  { color: 'processing', text: '合成中' },
  ready:      { color: 'warning',    text: '待上传' },
  uploading:  { color: 'processing', text: '上传中' },
  uploaded:   { color: 'success',    text: '已上传' },
  failed:     { color: 'error',      text: '失败' },
  cancelled:  { color: 'default',    text: '已取消' },
}

const STATUS_FILTER_OPTIONS = (Object.keys(statusMap) as TaskStatus[]).map((key) => ({
  text: statusMap[key].text,
  value: key,
}))

export default function TaskList() {
  const navigate = useNavigate()

  const { data: tasksData, isLoading, refetch: refetchTasks } = useTasks()
  const { data: accounts = [] } = useAccounts()
  const { data: videos = [] } = useVideos()
  const deleteTask = useDeleteTask()
  const deleteAllTasks = useDeleteAllTasks()

  const tasks = tasksData?.items as unknown as Task[] ?? []

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTask.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('删除失败')
      }
    }
  }, [deleteTask])

  const handleClearAll = useCallback(async () => {
    try {
      await deleteAllTasks.mutateAsync()
      message.success('已清空所有任务')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('清空失败')
      }
    }
  }, [deleteAllTasks])

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '账号',
      dataIndex: 'account_id',
      key: 'account_id',
      width: 120,
      render: (id: number) =>
        accounts.find((a: AccountResponseExtended) => a.id === id)?.account_name || `ID:${id}`,
    },
    {
      title: '视频名称',
      dataIndex: 'video_id',
      key: 'video_id',
      ellipsis: true,
      render: (videoId: number | null | undefined) => {
        if (videoId) {
          const video = videos.find((v: VideoResponse) => v.id === videoId)
          if (video) return <span style={{ fontSize: 12 }}>{video.name}</span>
        }
        return '-'
      },
    },
    {
      title: '话题标签',
      dataIndex: 'topic_ids',
      key: 'topic_ids',
      width: 160,
      render: (topicIds: number[] | null | undefined) => {
        if (topicIds && topicIds.length > 0) {
          return (
            <Space size={2} wrap>
              {topicIds.map(tid => (
                <Tag key={tid} style={{ fontSize: 11, margin: 0 }}>#{tid}</Tag>
              ))}
            </Space>
          )
        }
        return '-'
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      filters: STATUS_FILTER_OPTIONS,
      onFilter: (value: unknown, record: Task) => record.status === value,
      render: (status: TaskStatus, record: Task) => {
        const { color, text } = statusMap[status] ?? { color: 'default', text: status }
        const tag = <Tag color={color}>{text}</Tag>
        if (status === 'failed' && record.error_msg) {
          return <Tooltip title={record.error_msg}>{tag}</Tooltip>
        }
        return tag
      },
    },
    {
      title: '发布时间',
      dataIndex: 'publish_time',
      key: 'publish_time',
      width: 160,
      render: (text: string | null) =>
        text ? new Date(text).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: Task) => (
        <Popconfirm title="确定删除该任务？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" size="small" danger loading={deleteTask.isPending}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      {/* 操作栏 */}
      <Row justify="space-between" style={{ marginBottom: 16 }}>
        <Col>
          <Space>
            <Button type="primary" icon={<AppstoreAddOutlined />} onClick={() => navigate('/task/assemble')}>
              组装任务
            </Button>
            <Popconfirm title="确定清空所有任务？" onConfirm={handleClearAll}>
              <Button danger>清空所有</Button>
            </Popconfirm>
          </Space>
        </Col>
        <Col>
          <Button icon={<ReloadOutlined />} onClick={() => refetchTasks()}>
            刷新
          </Button>
        </Col>
      </Row>

      <Table<Task>
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 15 }}
        size="small"
        scroll={{ x: 1000 }}
        onRow={(record) => ({
          onClick: () => navigate(`/task/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </>
  )
}
