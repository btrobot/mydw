import { useState, useCallback } from 'react'
import {
  Table, Tag, Button, Space, Modal, Form, Select,
  message, Popconfirm, Row, Col, Card, Statistic, Tooltip,
  Descriptions, Progress, Alert, Typography, Spin,
} from 'antd'
import {
  PlayCircleOutlined, PauseCircleOutlined,
  ReloadOutlined, SwapOutlined, AppstoreAddOutlined,
  StopOutlined,
} from '@ant-design/icons'
import axios from 'axios'
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
  useRetryTask,
  useEditRetryTask,
  useCancelTask,
  useSubmitComposition,
  useCompositionStatus,
  useCancelComposition,
} from '../hooks'
import { useVideos } from '../hooks/useVideo'
import { useCovers } from '../hooks/useCover'
import { useAudios } from '../hooks/useAudio'
import { useCopywritings } from '../hooks/useCopywriting'
import { useProfiles } from '../hooks/useProfile'
import type { PublishProfileResponse } from '../hooks/useProfile'
import type { AccountResponseExtended } from '../hooks/useAccount'
import type { VideoResponse, CopywritingResponse, AudioResponse, CoverResponse } from '@/types/material'

const { Text, Link } = Typography

// 7-state enum aligned with backend TaskStatus
type TaskStatus =
  | 'draft'
  | 'composing'
  | 'ready'
  | 'uploading'
  | 'uploaded'
  | 'failed'
  | 'cancelled'

// Terminal states — no further transitions expected
const TERMINAL_STATES: ReadonlySet<TaskStatus> = new Set<TaskStatus>([
  'uploaded',
  'failed',
  'cancelled',
])

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

interface TaskStats {
  total: number
  draft: number
  composing: number
  ready: number
  uploading: number
  uploaded: number
  failed: number
  cancelled: number
  today_success: number
}

interface AssembleFormValues {
  video_ids: number[]
  account_ids: number[]
  strategy: string
  copywriting_mode: string
  profile_id?: number | null
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

const COMPOSITION_MODE_LABEL: Record<string, string> = {
  none: '无需合成',
  coze: 'Coze 合成',
  local_ffmpeg: '本地 FFmpeg 合成',
}

export default function Task() {
  const [assembleVisible, setAssembleVisible] = useState(false)
  const [assembleForm] = Form.useForm<AssembleFormValues>()
  const [selectedCompositionMode, setSelectedCompositionMode] = useState<string | null>(null)

  const { data: tasksData, isLoading, refetch: refetchTasks } = useTasks()
  const { data: accounts = [] } = useAccounts()
  const { data: videos = [] } = useVideos()
  const { data: covers = [] } = useCovers()
  const { data: profilesData } = useProfiles()
  const { data: publishStatus = { status: 'idle', current_task_id: null, total_pending: 0, total_success: 0, total_failed: 0 } } = usePublishStatus()
  const { data: stats } = useTaskStats()

  const controlPublish = useControlPublish()
  const shuffleTasks = useShuffleTasks()
  const deleteTask = useDeleteTask()
  const deleteAllTasks = useDeleteAllTasks()
  const assembleTasks = useAssembleTasks()
  const retryTask = useRetryTask()
  const editRetryTask = useEditRetryTask()
  const cancelTask = useCancelTask()

  // Cast stats to new shape; fall back to zeros while API types are regenerated
  const typedStats = stats as unknown as TaskStats | undefined
  const safeStats: TaskStats = {
    total:     typedStats?.total     ?? 0,
    draft:     typedStats?.draft     ?? 0,
    composing: typedStats?.composing ?? 0,
    ready:     typedStats?.ready     ?? 0,
    uploading: typedStats?.uploading ?? 0,
    uploaded:  typedStats?.uploaded  ?? 0,
    failed:    typedStats?.failed    ?? 0,
    cancelled: typedStats?.cancelled ?? 0,
    today_success: typedStats?.today_success ?? 0,
  }

  const tasks = tasksData?.items as unknown as Task[] ?? []

  const handlePublish = useCallback(async (action: 'start' | 'pause' | 'stop') => {
    try {
      await controlPublish.mutateAsync({ action })
      message.success(
        action === 'start' ? '开始发布'
          : action === 'pause' ? '暂停发布'
          : '停止发布'
      )
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

  const handleRetry = useCallback(async (id: number) => {
    try {
      await retryTask.mutateAsync(id)
      message.success('已重新加入队列')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('重试失败')
      }
    }
  }, [retryTask])

  const handleEditRetry = useCallback(async (id: number) => {
    try {
      await editRetryTask.mutateAsync(id)
      message.success('已重置为草稿')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('编辑重试失败')
      }
    }
  }, [editRetryTask])

  const handleCancel = useCallback(async (id: number) => {
    try {
      await cancelTask.mutateAsync(id)
      message.success('任务已取消')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('取消失败')
      }
    }
  }, [cancelTask])

  const profiles = profilesData?.items ?? []

  const handleAssembleOpen = useCallback(() => {
    const defaultProfile = profiles.find((p: PublishProfileResponse) => p.is_default)
    assembleForm.resetFields()
    if (defaultProfile) {
      assembleForm.setFieldValue('profile_id', defaultProfile.id)
      setSelectedCompositionMode(defaultProfile.composition_mode)
    } else {
      setSelectedCompositionMode(null)
    }
    setAssembleVisible(true)
  }, [assembleForm, profiles])

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
      width: 180,
      render: (_: unknown, record: Task) => {
        const isFailed = record.status === 'failed'
        const isTerminal = TERMINAL_STATES.has(record.status)
        return (
          <Space size={4}>
            {isFailed && (
              <Tooltip title="重新加入上传队列">
                <Button
                  type="link"
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={() => handleRetry(record.id)}
                  loading={retryTask.isPending}
                >
                  重试
                </Button>
              </Tooltip>
            )}
            {isFailed && (
              <Tooltip title="重置为草稿重新编辑">
                <Button
                  type="link"
                  size="small"
                  onClick={() => handleEditRetry(record.id)}
                  loading={editRetryTask.isPending}
                >
                  编辑重试
                </Button>
              </Tooltip>
            )}
            {!isTerminal && (
              <Popconfirm title="确定取消该任务？" onConfirm={() => handleCancel(record.id)}>
                <Button
                  type="link"
                  size="small"
                  icon={<StopOutlined />}
                  loading={cancelTask.isPending}
                >
                  取消
                </Button>
              </Popconfirm>
            )}
            <Button type="link" size="small" danger onClick={() => handleDelete(record.id)}>
              删除
            </Button>
          </Space>
        )
      },
    },
  ]

  return (
    <>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={3}>
          <Card size="small">
            <Statistic title="总计" value={safeStats.total} />
          </Card>
        </Col>
        <Col span={3}>
          <Card size="small">
            <Statistic title="草稿" value={safeStats.draft} valueStyle={{ color: '#999' }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card size="small">
            <Statistic title="合成中" value={safeStats.composing} valueStyle={{ color: '#1677ff' }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card size="small">
            <Statistic title="待上传" value={safeStats.ready} valueStyle={{ color: '#d46b08' }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card size="small">
            <Statistic title="上传中" value={safeStats.uploading} valueStyle={{ color: '#1677ff' }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card size="small">
            <Statistic title="已上传" value={safeStats.uploaded} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card size="small">
            <Statistic title="失败" value={safeStats.failed} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={3}>
          <Card size="small">
            <Statistic title="今日上传" value={safeStats.today_success} valueStyle={{ color: '#3f8600' }} />
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
        scroll={{ x: 1000 }}
      />

      {/* 组装任务 Modal */}
      <Modal
        title="组装任务"
        open={assembleVisible}
        onOk={handleAssembleSubmit}
        onCancel={() => setAssembleVisible(false)}
        confirmLoading={assembleTasks.isPending}
        width={520}
        destroyOnHidden
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
          <Form.Item name="cover_id" label="封面（可选）">
            <Select
              allowClear
              placeholder="选择封面"
              options={covers.map((c) => ({ value: c.id, label: c.file_path.split(/[/\\]/).pop() ?? `封面 #${c.id}` }))}
            />
          </Form.Item>
          <Form.Item name="profile_id" label="发布配置档（可选）">
            <Select
              allowClear
              placeholder="选择配置档（不选则使用默认）"
              optionFilterProp="label"
              onChange={(value: number | null | undefined) => {
                const profile = profiles.find((p: PublishProfileResponse) => p.id === value)
                setSelectedCompositionMode(profile?.composition_mode ?? null)
              }}
              options={profiles.map((p: PublishProfileResponse) => ({
                value: p.id,
                label: p.is_default ? `${p.name}（默认）` : p.name,
              }))}
            />
          </Form.Item>
          {selectedCompositionMode !== null && (
            <Form.Item>
              <Text type="secondary">
                合成方式：{COMPOSITION_MODE_LABEL[selectedCompositionMode] ?? selectedCompositionMode}
              </Text>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  )
}
