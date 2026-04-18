import { useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Divider,
  Flex,
  Popconfirm,
  Progress,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  DeleteOutlined,
  EditOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  StopOutlined,
} from '@ant-design/icons'

import type { TaskResponse } from '@/api'
import {
  useCancelComposition,
  useCancelTask,
  useCompositionStatus,
  useDeleteTask,
  useEditRetryTask,
  useRetryTask,
  useSubmitComposition,
  useTask,
} from '@/hooks'
import { useProfiles } from '@/hooks/useProfile'
import { handleApiError } from '@/utils/error'

import { getTaskSemanticsSummary } from './taskSemantics'

const { Text } = Typography

type TaskStatus = 'draft' | 'composing' | 'ready' | 'uploading' | 'uploaded' | 'failed' | 'cancelled'

const statusMap: Record<TaskStatus, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  composing: { color: 'processing', text: '合成中' },
  ready: { color: 'warning', text: '待上传' },
  uploading: { color: 'processing', text: '上传中' },
  uploaded: { color: 'success', text: '已上传' },
  failed: { color: 'error', text: '失败' },
  cancelled: { color: 'default', text: '已取消' },
}

const TERMINAL_STATES: ReadonlySet<TaskStatus> = new Set<TaskStatus>(['uploaded', 'cancelled'])

const priorityLabel = (priority: number): string => {
  if (priority >= 10) return '高'
  if (priority >= 5) return '中'
  return '低'
}

const priorityColor = (priority: number): string => {
  if (priority >= 10) return 'red'
  if (priority >= 5) return 'orange'
  return 'default'
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const taskId = id ? Number.parseInt(id, 10) : undefined

  const { data: task, isLoading } = useTask(taskId ?? 0)
  const { data: profilesData } = useProfiles()
  const profiles = profilesData?.items ?? []

  const compositionQuery = useCompositionStatus(taskId ?? null)
  const compositionJob = compositionQuery.data

  const submitComposition = useSubmitComposition()
  const cancelComposition = useCancelComposition()
  const retryTask = useRetryTask()
  const editRetryTask = useEditRetryTask()
  const cancelTask = useCancelTask()
  const deleteTask = useDeleteTask()

  const handleSubmitComposition = useCallback(async () => {
    if (!taskId) return
    try {
      await submitComposition.mutateAsync(taskId)
      message.success('已提交合成任务')
    } catch (error: unknown) {
      handleApiError(error, '提交合成失败')
    }
  }, [submitComposition, taskId])

  const handleCancelComposition = useCallback(async () => {
    if (!taskId) return
    try {
      await cancelComposition.mutateAsync(taskId)
      message.success('已取消合成任务')
    } catch (error: unknown) {
      handleApiError(error, '取消合成失败')
    }
  }, [cancelComposition, taskId])

  const handleRetry = useCallback(async () => {
    if (!taskId) return
    try {
      await retryTask.mutateAsync(taskId)
      message.success('已发起任务重试')
    } catch (error: unknown) {
      handleApiError(error, '重试任务失败')
    }
  }, [retryTask, taskId])

  const handleEditRetry = useCallback(async () => {
    if (!taskId) return
    try {
      await editRetryTask.mutateAsync(taskId)
      message.success('已创建可编辑重试任务')
      navigate(-1)
    } catch (error: unknown) {
      handleApiError(error, '创建可编辑重试任务失败')
    }
  }, [editRetryTask, navigate, taskId])

  const handleCancel = useCallback(async () => {
    if (!taskId) return
    try {
      await cancelTask.mutateAsync(taskId)
      message.success('已取消任务')
    } catch (error: unknown) {
      handleApiError(error, '取消任务失败')
    }
  }, [cancelTask, taskId])

  const handleDelete = useCallback(async () => {
    if (!taskId) return
    try {
      await deleteTask.mutateAsync(taskId)
      message.success('已删除任务')
      navigate(-1)
    } catch (error: unknown) {
      handleApiError(error, '删除任务失败')
    }
  }, [deleteTask, navigate, taskId])

  if (isLoading) {
    return <Flex justify="center" style={{ padding: 48 }}><Spin size="large" /></Flex>
  }

  if (!task) {
    return (
      <Flex vertical gap={16} style={{ padding: 24 }}>
        <Button type="link" onClick={() => navigate(-1)} style={{ alignSelf: 'flex-start', padding: 0 }}>返回</Button>
        <Alert type="error" message="任务不存在或已被删除" />
      </Flex>
    )
  }

  const { color: statusColor, text: statusText } = statusMap[task.status] ?? { color: 'default', text: task.status }
  const isComposing = task.status === 'draft' || task.status === 'composing'
  const isUploaded = task.status === 'uploaded'
  const isFailed = task.status === 'failed'
  const isTerminal = TERMINAL_STATES.has(task.status)
  const compositionActive = compositionJob?.status === 'pending' || compositionJob?.status === 'processing'
  const semantics = getTaskSemanticsSummary(task as TaskResponse, profiles)
  const renderIds = (ids?: number[]) => (ids && ids.length > 0 ? ids.map((item) => `#${item}`).join(', ') : '-')

  return (
    <Flex vertical gap={16} style={{ padding: 24, maxWidth: 960 }} data-testid="task-detail-page">
      <Flex justify="space-between" align="center" wrap="wrap" gap={12}>
        <Space wrap>
          <Button onClick={() => navigate(-1)}>返回上一页</Button>
          <Button onClick={() => navigate('/creative/workbench')} data-testid="task-detail-open-workbench">返回作品工作台</Button>
          {task.creative_item_id ? <Button type="primary" onClick={() => navigate(`/creative/${task.creative_item_id}`)} data-testid="task-detail-open-creative">返回作品详情</Button> : null}
        </Space>
        <Tag color={statusColor} style={{ fontSize: 14, padding: '2px 10px' }}>{statusText}</Tag>
      </Flex>

      <Alert type="info" showIcon data-testid="task-detail-diagnostics-banner" message={`任务 #${task.id} 执行 / 诊断页`} description="这里用于查看任务执行、重试、发布链路与排障细节；作品业务状态仍以作品详情页为准。" />

      <Card title="基本信息" size="small">
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="任务 ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={statusColor}>{statusText}</Tag></Descriptions.Item>
          <Descriptions.Item label="账号">{task.account_name ? `${task.account_name} (${task.account_id})` : task.account_id}</Descriptions.Item>
          <Descriptions.Item label="Profile ID">{task.profile_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="作品 ID">{task.creative_item_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="作品版本 ID">{task.creative_version_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="优先级"><Tag color={priorityColor(task.priority)}>{priorityLabel(task.priority)} ({task.priority})</Tag></Descriptions.Item>
          <Descriptions.Item label="计划发布时间">{task.scheduled_time ? new Date(task.scheduled_time).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(task.created_at).toLocaleString('zh-CN')}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{new Date(task.updated_at).toLocaleString('zh-CN')}</Descriptions.Item>
          {isFailed && task.error_msg ? <Descriptions.Item label="错误信息" span={2}><Text type="danger">{task.error_msg}</Text></Descriptions.Item> : null}
        </Descriptions>
      </Card>

      <Card title="执行语义" size="small">
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label="模式">{semantics.modeLabel}</Descriptions.Item>
          <Descriptions.Item label="可直接发布"><Tag color={semantics.directPublishAllowed ? 'success' : 'warning'}>{semantics.directPublishAllowed ? '兼容' : '不兼容'}</Tag></Descriptions.Item>
          <Descriptions.Item label="最终发布视频来源">{semantics.usesFinalVideo ? '使用 final_video_path 作为最终成片' : '使用素材集合参与发布'}</Descriptions.Item>
          <Descriptions.Item label="语义说明">{semantics.mode === 'none' ? '直接发布要求最终成片唯一，且文案、封面数量受限；独立音频需先进入合成流程。' : '当前任务使用合成模式，需先完成合成，再进入发布链路。'}</Descriptions.Item>
        </Descriptions>
        {semantics.violations.length > 0 ? (
          <>
            <Divider />
            <Alert
              type="warning"
              showIcon
              message="当前任务存在直接发布语义警告"
              description={<ul style={{ margin: 0, paddingInlineStart: 18 }}>{semantics.violations.map((item) => <li key={item}>{item}</li>)}</ul>}
            />
          </>
        ) : null}
      </Card>

      <Card title="素材信息" size="small">
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label={`视频（${task.video_ids?.length ?? 0}）`}>{renderIds(task.video_ids)}</Descriptions.Item>
          <Descriptions.Item label={`文案（${task.copywriting_ids?.length ?? 0}）`}>{renderIds(task.copywriting_ids)}</Descriptions.Item>
          <Descriptions.Item label={`封面（${task.cover_ids?.length ?? 0}）`}>{renderIds(task.cover_ids)}</Descriptions.Item>
          <Descriptions.Item label={`音频（${task.audio_ids?.length ?? 0}）`}>{renderIds(task.audio_ids)}</Descriptions.Item>
          <Descriptions.Item label={`话题（${task.topic_ids?.length ?? 0}）`}>{renderIds(task.topic_ids)}</Descriptions.Item>
          <Descriptions.Item label="最终成片路径">{task.final_video_path ?? '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {isComposing ? (
        <Card title="合成执行" size="small">
          {compositionActive && compositionJob ? (
            <Flex vertical gap={12}>
              <Flex align="center" gap={12}><Text>当前进度</Text><Progress percent={compositionJob.progress} status="active" style={{ flex: 1 }} /><Text type="secondary">{compositionJob.status}</Text></Flex>
              {compositionJob.error_msg ? <Alert type="error" message={compositionJob.error_msg} /> : null}
              <Flex justify="flex-end"><Popconfirm title="确认取消当前合成吗？" onConfirm={() => void handleCancelComposition()}><Button danger icon={<StopOutlined />} loading={cancelComposition.isPending}>取消合成</Button></Popconfirm></Flex>
            </Flex>
          ) : (
            <Flex vertical gap={12}>
              {compositionJob?.status === 'failed' && compositionJob.error_msg ? <Alert type="error" message={`合成失败：${compositionJob.error_msg}`} /> : null}
              <Flex justify="flex-end"><Button type="primary" icon={<PlayCircleOutlined />} loading={submitComposition.isPending} onClick={() => void handleSubmitComposition()}>提交合成</Button></Flex>
            </Flex>
          )}
        </Card>
      ) : null}

      {isUploaded ? (
        <Card title="上传结果" size="small">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="得物视频 ID">{task.dewu_video_id ?? '-'}</Descriptions.Item>
            <Descriptions.Item label="上传地址">{task.upload_url ? <a href={task.upload_url} target="_blank" rel="noreferrer">{task.upload_url}</a> : '-'}</Descriptions.Item>
          </Descriptions>
        </Card>
      ) : null}

      <Card title="任务动作" size="small">
        <Space wrap>
          {isFailed ? <Button icon={<ReloadOutlined />} loading={retryTask.isPending} onClick={() => void handleRetry()}>重试</Button> : null}
          {isFailed ? <Button icon={<EditOutlined />} loading={editRetryTask.isPending} onClick={() => void handleEditRetry()}>创建可编辑重试</Button> : null}
          {!isTerminal ? <Popconfirm title="确认取消这个任务吗？" onConfirm={() => void handleCancel()}><Button icon={<StopOutlined />} loading={cancelTask.isPending}>取消任务</Button></Popconfirm> : null}
          <Popconfirm title="确认删除这个任务吗？删除后不可恢复。" onConfirm={() => void handleDelete()}><Button danger icon={<DeleteOutlined />} loading={deleteTask.isPending}>删除</Button></Popconfirm>
        </Space>
      </Card>
    </Flex>
  )
}
