import { useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Card, Tag, Space, message, Spin, Flex, Typography,
  Descriptions, Progress, Popconfirm, Alert, Divider,
} from 'antd'
import {
  ReloadOutlined, EditOutlined, StopOutlined, DeleteOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons'
import {
  useTask,
  useSubmitComposition,
  useCompositionStatus,
  useCancelComposition,
  useRetryTask,
  useEditRetryTask,
  useCancelTask,
  useDeleteTask,
} from '@/hooks'
import { useProfiles } from '@/hooks/useProfile'
import { handleApiError } from '@/utils/error'
import type { TaskResponse } from '@/api'
import { getTaskSemanticsSummary } from './taskSemantics'

const { Text, Title } = Typography

// 7-state enum aligned with backend TaskStatus (FE-TM-04)
type TaskStatus =
  | 'draft'
  | 'composing'
  | 'ready'
  | 'uploading'
  | 'uploaded'
  | 'failed'
  | 'cancelled'

const statusMap: Record<TaskStatus, { color: string; text: string }> = {
  draft:      { color: 'default',    text: '草稿' },
  composing:  { color: 'processing', text: '合成中' },
  ready:      { color: 'warning',    text: '待上传' },
  uploading:  { color: 'processing', text: '上传中' },
  uploaded:   { color: 'success',    text: '已上传' },
  failed:     { color: 'error',      text: '失败' },
  cancelled:  { color: 'default',    text: '已取消' },
}

const TERMINAL_STATES: ReadonlySet<TaskStatus> = new Set<TaskStatus>([
  'uploaded',
  'cancelled',
])

const priorityLabel = (p: number): string => {
  if (p >= 10) return '高'
  if (p >= 5)  return '中'
  return '低'
}

const priorityColor = (p: number): string => {
  if (p >= 10) return 'red'
  if (p >= 5)  return 'orange'
  return 'default'
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const taskId = id ? parseInt(id, 10) : undefined

  const { data: task, isLoading } = useTask(taskId ?? 0)
  const { data: profilesData } = useProfiles()
  const profiles = profilesData?.items ?? []

  // Composition status polling — only active when task exists
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
  }, [taskId, submitComposition])

  const handleCancelComposition = useCallback(async () => {
    if (!taskId) return
    try {
      await cancelComposition.mutateAsync(taskId)
      message.success('已取消合成')
    } catch (error: unknown) {
      handleApiError(error, '取消合成失败')
    }
  }, [taskId, cancelComposition])

  const handleRetry = useCallback(async () => {
    if (!taskId) return
    try {
      await retryTask.mutateAsync(taskId)
      message.success('已重新加入队列')
    } catch (error: unknown) {
      handleApiError(error, '重试失败')
    }
  }, [taskId, retryTask])

  const handleEditRetry = useCallback(async () => {
    if (!taskId) return
    try {
      await editRetryTask.mutateAsync(taskId)
      message.success('已重置为草稿')
      navigate(-1)
    } catch (error: unknown) {
      handleApiError(error, '编辑重试失败')
    }
  }, [taskId, editRetryTask, navigate])

  const handleCancel = useCallback(async () => {
    if (!taskId) return
    try {
      await cancelTask.mutateAsync(taskId)
      message.success('任务已取消')
    } catch (error: unknown) {
      handleApiError(error, '取消失败')
    }
  }, [taskId, cancelTask])

  const handleDelete = useCallback(async () => {
    if (!taskId) return
    try {
      await deleteTask.mutateAsync(taskId)
      message.success('删除成功')
      navigate(-1)
    } catch (error: unknown) {
      handleApiError(error, '删除失败')
    }
  }, [taskId, deleteTask, navigate])

  if (isLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (!task) {
    return (
      <Flex vertical gap={16} style={{ padding: 24 }}>
        <Button type="link" onClick={() => navigate(-1)} style={{ alignSelf: 'flex-start', padding: 0 }}>
          返回
        </Button>
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
    <Flex vertical gap={16} style={{ padding: 24, maxWidth: 900 }}>
      {/* Header */}
      <Flex justify="space-between" align="center">
        <Space>
          <Button onClick={() => navigate(-1)}>返回</Button>
          <Title level={4} style={{ margin: 0 }}>任务详情 #{task.id}</Title>
        </Space>
        <Tag color={statusColor} style={{ fontSize: 14, padding: '2px 10px' }}>{statusText}</Tag>
      </Flex>

      {/* Card 1: 基本信息 */}
      <Card title="基本信息" size="small">
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="任务 ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColor}>{statusText}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="账号 ID">
            {task.account_name ? `${task.account_name} (${task.account_id})` : task.account_id}
          </Descriptions.Item>
          <Descriptions.Item label="配置档 ID">
            {task.profile_id ?? '-'}
          </Descriptions.Item>
          <Descriptions.Item label="优先级">
            <Tag color={priorityColor(task.priority)}>
              {priorityLabel(task.priority)} ({task.priority})
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="计划发布时间">
            {task.scheduled_time ? new Date(task.scheduled_time).toLocaleString('zh-CN') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(task.created_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(task.updated_at).toLocaleString('zh-CN')}
          </Descriptions.Item>
          {isFailed && task.error_msg && (
            <Descriptions.Item label="错误信息" span={2}>
              <Text type="danger">{task.error_msg}</Text>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* Card 2: 执行语义 */}
      <Card title="执行语义" size="small">
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label="模式">
            {semantics.modeLabel}
          </Descriptions.Item>
          <Descriptions.Item label="直接发布是否满足当前语义">
            <Tag color={semantics.directPublishAllowed ? 'success' : 'warning'}>
              {semantics.directPublishAllowed ? '满足' : '不满足'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="最终发布视频来源">
            {semantics.usesFinalVideo ? '使用 final_video_path（合成产物）' : '使用视频资源集合'}
          </Descriptions.Item>
          <Descriptions.Item label="语义说明">
            {semantics.mode === 'none'
              ? '直接发布模式：仅支持 1 个最终视频、0/1 个文案、0/1 个封面；多话题允许；独立音频需先合成。'
              : '合成模式：多视频 / 多文案 / 多封面 / 音频属于合成输入；最终直接发布使用合成后的 final video。'}
          </Descriptions.Item>
        </Descriptions>
        {semantics.violations.length > 0 && (
          <>
            <Divider />
            <Alert
              type="warning"
              showIcon
              message="当前任务语义提示"
              description={
                <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                  {semantics.violations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              }
            />
          </>
        )}
      </Card>

      {/* Card 3: 素材集合 */}
      <Card title="素材集合" size="small">
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label={`视频（${task.video_ids?.length ?? 0}）`}>
            {renderIds(task.video_ids)}
          </Descriptions.Item>
          <Descriptions.Item label={`文案（${task.copywriting_ids?.length ?? 0}）`}>
            {renderIds(task.copywriting_ids)}
          </Descriptions.Item>
          <Descriptions.Item label={`封面（${task.cover_ids?.length ?? 0}）`}>
            {renderIds(task.cover_ids)}
          </Descriptions.Item>
          <Descriptions.Item label={`音频（${task.audio_ids?.length ?? 0}）`}>
            {renderIds(task.audio_ids)}
          </Descriptions.Item>
          <Descriptions.Item label={`话题（${task.topic_ids?.length ?? 0}）`}>
            {renderIds(task.topic_ids)}
          </Descriptions.Item>
          <Descriptions.Item label="Final Video Path">
            {task.final_video_path ?? '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Card 4: 合成 (draft / composing 状态显示) */}
      {isComposing && (
        <Card title="合成" size="small">
          {compositionActive && compositionJob ? (
            <Flex vertical gap={12}>
              <Flex align="center" gap={12}>
                <Text>合成进度</Text>
                <Progress
                  percent={compositionJob.progress}
                  status="active"
                  style={{ flex: 1 }}
                />
                <Text type="secondary">{compositionJob.status}</Text>
              </Flex>
              {compositionJob.error_msg && (
                <Alert type="error" message={compositionJob.error_msg} />
              )}
              <Flex justify="flex-end">
                <Popconfirm title="确定取消合成？" onConfirm={handleCancelComposition}>
                  <Button
                    danger
                    icon={<StopOutlined />}
                    loading={cancelComposition.isPending}
                  >
                    取消合成
                  </Button>
                </Popconfirm>
              </Flex>
            </Flex>
          ) : (
            <Flex vertical gap={12}>
              {compositionJob?.status === 'failed' && compositionJob.error_msg && (
                <Alert type="error" message={`合成失败: ${compositionJob.error_msg}`} />
              )}
              <Flex justify="flex-end">
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  loading={submitComposition.isPending}
                  onClick={handleSubmitComposition}
                >
                  提交合成
                </Button>
              </Flex>
            </Flex>
          )}
        </Card>
      )}

      {/* Card 5: 上传结果 (uploaded 状态显示) */}
      {isUploaded && (
        <Card title="上传结果" size="small">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="得物视频 ID">
              {task.dewu_video_id ?? '-'}
            </Descriptions.Item>
            <Descriptions.Item label="视频链接">
              {task.upload_url ? (
                <a href={task.upload_url} target="_blank" rel="noreferrer">
                  {task.upload_url}
                </a>
              ) : '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* 操作区 */}
      <Card title="操作" size="small">
        <Space wrap>
          {isFailed && (
            <Button
              icon={<ReloadOutlined />}
              loading={retryTask.isPending}
              onClick={handleRetry}
            >
              重试
            </Button>
          )}
          {isFailed && (
            <Button
              icon={<EditOutlined />}
              loading={editRetryTask.isPending}
              onClick={handleEditRetry}
            >
              编辑重试
            </Button>
          )}
          {!isTerminal && (
            <Popconfirm title="确定取消该任务？" onConfirm={handleCancel}>
              <Button
                icon={<StopOutlined />}
                loading={cancelTask.isPending}
              >
                取消任务
              </Button>
            </Popconfirm>
          )}
          <Popconfirm title="确定删除该任务？删除后不可恢复。" onConfirm={handleDelete}>
            <Button
              danger
              icon={<DeleteOutlined />}
              loading={deleteTask.isPending}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      </Card>
    </Flex>
  )
}
