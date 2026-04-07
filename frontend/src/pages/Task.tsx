import { useState, useCallback } from 'react'
import {
  Table, Tag, Button, Space, Modal, Form, Select,
  message, Popconfirm, Row, Col, Card, Statistic
} from 'antd'
import {
  PlayCircleOutlined, PauseCircleOutlined,
  ReloadOutlined, SwapOutlined, AppstoreAddOutlined,
} from '@ant-design/icons'
import {
  useTasks,
  useAccounts,
  usePublishStatus,
  useTaskStats,
  useControlPublish,
  useShuffleTasks,
  useDeleteTask,
  useDeleteAllTasks,
  useAssembleTasks,
} from '../hooks'
import { useVideos } from '../hooks/useVideo'
import type { AccountResponseExtended } from '../hooks/useAccount'
import type { VideoResponse } from '@/types/material'

interface Task {
  id: number
  account_id: number
  video_id?: number | null
  video_path?: string | null
  content?: string | null
  topic?: string | null
  topic_ids?: number[] | null
  cover_path?: string | null
  status: string
  publish_time?: string | null
  error_msg?: string | null
  priority: number
  created_at: string
}

interface AssembleFormValues {
  video_ids: number[]
  account_ids: number[]
  strategy: string
  copywriting_mode: string
}

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '待发布' },
  running: { color: 'processing', text: '发布中' },
  success: { color: 'success', text: '已发布' },
  failed: { color: 'error', text: '失败' },
  paused: { color: 'warning', text: '已暂停' },
}

export default function Task() {
  const [assembleVisible, setAssembleVisible] = useState(false)
  const [assembleForm] = Form.useForm<AssembleFormValues>()

  const { data: tasksData, isLoading, refetch: refetchTasks } = useTasks()
  const { data: accounts = [] } = useAccounts()
  const { data: videos = [] } = useVideos()
  const { data: publishStatus = { status: 'idle', current_task_id: null, total_pending: 0, total_success: 0, total_failed: 0 } } = usePublishStatus()
  const { data: stats = { total: 0, pending: 0, running: 0, success: 0, failed: 0, paused: 0, today_success: 0 } } = useTaskStats()

  const controlPublish = useControlPublish()
  const shuffleTasks = useShuffleTasks()
  const deleteTask = useDeleteTask()
  const deleteAllTasks = useDeleteAllTasks()
  const assembleTasks = useAssembleTasks()

  const tasks = tasksData?.items || []

  const handlePublish = useCallback(async (action: 'start' | 'pause' | 'stop') => {
    try {
      await controlPublish.mutateAsync({ action })
      message.success(action === 'start' ? '开始发布' : action === 'pause' ? '暂停发布' : '停止发布')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('操作失败')
      }
    }
  }, [controlPublish])

  const handleShuffle = useCallback(async () => {
    try {
      await shuffleTasks.mutateAsync()
      message.success('任务顺序已打乱')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('操作失败')
      }
    }
  }, [shuffleTasks])

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

  const handleAssembleOpen = useCallback(() => {
    assembleForm.resetFields()
    setAssembleVisible(true)
  }, [assembleForm])

  const handleAssembleSubmit = useCallback(async () => {
    try {
      const values = await assembleForm.validateFields()
      const result = await assembleTasks.mutateAsync(values)
      const count = Array.isArray(result) ? result.length : 0
      message.success(`组装成功，共生成 ${count} 个任务`)
      setAssembleVisible(false)
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('组装失败')
      }
    }
  }, [assembleForm, assembleTasks])

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
      render: (videoId: number | null | undefined, record: Task) => {
        if (videoId) {
          const video = videos.find((v: VideoResponse) => v.id === videoId)
          if (video) return <span style={{ fontSize: 12 }}>{video.name}</span>
        }
        if (record.video_path) {
          return <span style={{ fontSize: 12 }}>{record.video_path.split(/[/\\]/).pop()}</span>
        }
        return '-'
      },
    },
    {
      title: '文案',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      width: 180,
    },
    {
      title: '话题标签',
      dataIndex: 'topic_ids',
      key: 'topic_ids',
      width: 160,
      render: (topicIds: number[] | null | undefined, record: Task) => {
        if (topicIds && topicIds.length > 0) {
          return (
            <Space size={2} wrap>
              {topicIds.map(tid => (
                <Tag key={tid} style={{ fontSize: 11, margin: 0 }}>#{tid}</Tag>
              ))}
            </Space>
          )
        }
        if (record.topic) {
          return <span style={{ fontSize: 12 }}>{record.topic}</span>
        }
        return '-'
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        const { color, text } = statusMap[status] || { color: 'default', text: status }
        return <Tag color={color}>{text}</Tag>
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
        <Button type="link" size="small" danger onClick={() => handleDelete(record.id)}>
          删除
        </Button>
      ),
    },
  ]

  return (
    <>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic title="总计" value={stats.total} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="待发布" value={stats.pending} valueStyle={{ color: '#999' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="今日发布" value={stats.today_success} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="发布成功" value={stats.success} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="发布失败" value={stats.failed} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="发布状态"
              value={
                publishStatus.status === 'running' ? '运行中'
                  : publishStatus.status === 'paused' ? '已暂停'
                  : '空闲'
              }
              valueStyle={{ color: publishStatus.status === 'running' ? '#3f8600' : '#999' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 控制按钮 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col flex="auto">
          <Space>
            <Button type="primary" icon={<AppstoreAddOutlined />} onClick={handleAssembleOpen}>
              组装任务
            </Button>
            <Popconfirm title="确定清空所有任务？" onConfirm={handleClearAll}>
              <Button danger>清空所有</Button>
            </Popconfirm>
          </Space>
        </Col>
        <Col>
          <Card size="small">
            <Space>
              <span>发布控制:</span>
              {publishStatus.status === 'running' ? (
                <Button size="small" icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>
                  暂停
                </Button>
              ) : (
                <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>
                  开始
                </Button>
              )}
              <Button size="small" icon={<ReloadOutlined />} onClick={() => refetchTasks()}>
                刷新
              </Button>
              <Button size="small" icon={<SwapOutlined />} onClick={handleShuffle}>
                乱序
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Table<Task>
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 15 }}
        size="small"
        scroll={{ x: 900 }}
      />

      {/* 组装任务 Modal */}
      <Modal
        title="组装任务"
        open={assembleVisible}
        onOk={handleAssembleSubmit}
        onCancel={() => setAssembleVisible(false)}
        confirmLoading={assembleTasks.isPending}
        width={520}
        destroyOnClose
      >
        <Form form={assembleForm} layout="vertical" initialValues={{ strategy: 'round_robin', copywriting_mode: 'auto_match' }}>
          <Form.Item
            name="video_ids"
            label="选择视频"
            rules={[{ required: true, message: '请选择至少一个视频' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择视频"
              optionFilterProp="label"
              options={videos.map((v: VideoResponse) => ({ value: v.id, label: v.name }))}
            />
          </Form.Item>
          <Form.Item
            name="account_ids"
            label="选择账号"
            rules={[{ required: true, message: '请选择至少一个账号' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择账号"
              optionFilterProp="label"
              options={accounts.map((a: AccountResponseExtended) => ({ value: a.id, label: a.account_name }))}
            />
          </Form.Item>
          <Form.Item name="strategy" label="分配策略">
            <Select
              options={[
                { value: 'round_robin', label: '轮询分配' },
                { value: 'manual', label: '手动分配' },
              ]}
            />
          </Form.Item>
          <Form.Item name="copywriting_mode" label="文案模式">
            <Select
              options={[
                { value: 'auto_match', label: '自动匹配' },
                { value: 'manual', label: '手动指定' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
