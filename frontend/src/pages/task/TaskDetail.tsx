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
  draft: { color: 'default', text: 'Draft' },
  composing: { color: 'processing', text: 'Composing' },
  ready: { color: 'warning', text: 'Ready' },
  uploading: { color: 'processing', text: 'Uploading' },
  uploaded: { color: 'success', text: 'Uploaded' },
  failed: { color: 'error', text: 'Failed' },
  cancelled: { color: 'default', text: 'Cancelled' },
}

const TERMINAL_STATES: ReadonlySet<TaskStatus> = new Set<TaskStatus>(['uploaded', 'cancelled'])

const priorityLabel = (priority: number): string => {
  if (priority >= 10) return 'High'
  if (priority >= 5) return 'Medium'
  return 'Low'
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
      message.success('Composition submitted')
    } catch (error: unknown) {
      handleApiError(error, 'Submit composition failed')
    }
  }, [submitComposition, taskId])

  const handleCancelComposition = useCallback(async () => {
    if (!taskId) return
    try {
      await cancelComposition.mutateAsync(taskId)
      message.success('Composition cancelled')
    } catch (error: unknown) {
      handleApiError(error, 'Cancel composition failed')
    }
  }, [cancelComposition, taskId])

  const handleRetry = useCallback(async () => {
    if (!taskId) return
    try {
      await retryTask.mutateAsync(taskId)
      message.success('Task queued again')
    } catch (error: unknown) {
      handleApiError(error, 'Retry failed')
    }
  }, [retryTask, taskId])

  const handleEditRetry = useCallback(async () => {
    if (!taskId) return
    try {
      await editRetryTask.mutateAsync(taskId)
      message.success('Task reset to draft')
      navigate(-1)
    } catch (error: unknown) {
      handleApiError(error, 'Edit retry failed')
    }
  }, [editRetryTask, navigate, taskId])

  const handleCancel = useCallback(async () => {
    if (!taskId) return
    try {
      await cancelTask.mutateAsync(taskId)
      message.success('Task cancelled')
    } catch (error: unknown) {
      handleApiError(error, 'Cancel failed')
    }
  }, [cancelTask, taskId])

  const handleDelete = useCallback(async () => {
    if (!taskId) return
    try {
      await deleteTask.mutateAsync(taskId)
      message.success('Task deleted')
      navigate(-1)
    } catch (error: unknown) {
      handleApiError(error, 'Delete failed')
    }
  }, [deleteTask, navigate, taskId])

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
          Back
        </Button>
        <Alert type="error" message="Task not found or already deleted" />
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
          <Button onClick={() => navigate(-1)}>Back</Button>
          <Button onClick={() => navigate('/creative/workbench')} data-testid="task-detail-open-workbench">
            Creative workbench
          </Button>
          {task.creative_item_id ? (
            <Button
              type="primary"
              onClick={() => navigate(`/creative/${task.creative_item_id}`)}
              data-testid="task-detail-open-creative"
            >
              Back to creative detail
            </Button>
          ) : null}
        </Space>
        <Tag color={statusColor} style={{ fontSize: 14, padding: '2px 10px' }}>{statusText}</Tag>
      </Flex>

      <Alert
        type="info"
        showIcon
        data-testid="task-detail-diagnostics-banner"
        message={`Execution / diagnostics task #${task.id}`}
        description="This page is for execution, retries, publish-chain inspection, and troubleshooting. Creative detail remains the source of truth for versions and review status."
      />

      <Card title="Basic info" size="small">
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="Task ID">{task.id}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={statusColor}>{statusText}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Account">
            {task.account_name ? `${task.account_name} (${task.account_id})` : task.account_id}
          </Descriptions.Item>
          <Descriptions.Item label="Profile ID">{task.profile_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Creative item ID">{task.creative_item_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Creative version ID">{task.creative_version_id ?? '-'}</Descriptions.Item>
          <Descriptions.Item label="Priority">
            <Tag color={priorityColor(task.priority)}>
              {priorityLabel(task.priority)} ({task.priority})
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Scheduled publish time">
            {task.scheduled_time ? new Date(task.scheduled_time).toLocaleString('zh-CN') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Created at">{new Date(task.created_at).toLocaleString('zh-CN')}</Descriptions.Item>
          <Descriptions.Item label="Updated at">{new Date(task.updated_at).toLocaleString('zh-CN')}</Descriptions.Item>
          {isFailed && task.error_msg ? (
            <Descriptions.Item label="Error" span={2}>
              <Text type="danger">{task.error_msg}</Text>
            </Descriptions.Item>
          ) : null}
        </Descriptions>
      </Card>

      <Card title="Execution semantics" size="small">
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label="Mode">{semantics.modeLabel}</Descriptions.Item>
          <Descriptions.Item label="Direct publish compatible">
            <Tag color={semantics.directPublishAllowed ? 'success' : 'warning'}>
              {semantics.directPublishAllowed ? 'Compatible' : 'Not compatible'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Final publish video source">
            {semantics.usesFinalVideo ? 'Uses final_video_path (composition output)' : 'Uses video resource collection'}
          </Descriptions.Item>
          <Descriptions.Item label="Semantics note">
            {semantics.mode === 'none'
              ? 'Direct publish expects a single final video, one copy item, and one cover. Independent audio must already be composed.'
              : 'Composition mode accepts multiple inputs and publishes the final composed video.'}
          </Descriptions.Item>
        </Descriptions>
        {semantics.violations.length > 0 ? (
          <>
            <Divider />
            <Alert
              type="warning"
              showIcon
              message="Current task semantic warnings"
              description={(
                <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                  {semantics.violations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
            />
          </>
        ) : null}
      </Card>

      <Card title="Materials" size="small">
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label={`Videos (${task.video_ids?.length ?? 0})`}>{renderIds(task.video_ids)}</Descriptions.Item>
          <Descriptions.Item label={`Copy (${task.copywriting_ids?.length ?? 0})`}>{renderIds(task.copywriting_ids)}</Descriptions.Item>
          <Descriptions.Item label={`Covers (${task.cover_ids?.length ?? 0})`}>{renderIds(task.cover_ids)}</Descriptions.Item>
          <Descriptions.Item label={`Audio (${task.audio_ids?.length ?? 0})`}>{renderIds(task.audio_ids)}</Descriptions.Item>
          <Descriptions.Item label={`Topics (${task.topic_ids?.length ?? 0})`}>{renderIds(task.topic_ids)}</Descriptions.Item>
          <Descriptions.Item label="Final video path">{task.final_video_path ?? '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {isComposing ? (
        <Card title="Composition" size="small">
          {compositionActive && compositionJob ? (
            <Flex vertical gap={12}>
              <Flex align="center" gap={12}>
                <Text>Composition progress</Text>
                <Progress percent={compositionJob.progress} status="active" style={{ flex: 1 }} />
                <Text type="secondary">{compositionJob.status}</Text>
              </Flex>
              {compositionJob.error_msg ? <Alert type="error" message={compositionJob.error_msg} /> : null}
              <Flex justify="flex-end">
                <Popconfirm title="Cancel composition?" onConfirm={() => void handleCancelComposition()}>
                  <Button danger icon={<StopOutlined />} loading={cancelComposition.isPending}>
                    Cancel composition
                  </Button>
                </Popconfirm>
              </Flex>
            </Flex>
          ) : (
            <Flex vertical gap={12}>
              {compositionJob?.status === 'failed' && compositionJob.error_msg ? (
                <Alert type="error" message={`Composition failed: ${compositionJob.error_msg}`} />
              ) : null}
              <Flex justify="flex-end">
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  loading={submitComposition.isPending}
                  onClick={() => void handleSubmitComposition()}
                >
                  Submit composition
                </Button>
              </Flex>
            </Flex>
          )}
        </Card>
      ) : null}

      {isUploaded ? (
        <Card title="Upload result" size="small">
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="Dewu video ID">{task.dewu_video_id ?? '-'}</Descriptions.Item>
            <Descriptions.Item label="Video URL">
              {task.upload_url ? (
                <a href={task.upload_url} target="_blank" rel="noreferrer">
                  {task.upload_url}
                </a>
              ) : '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      ) : null}

      <Card title="Actions" size="small">
        <Space wrap>
          {isFailed ? (
            <Button icon={<ReloadOutlined />} loading={retryTask.isPending} onClick={() => void handleRetry()}>
              Retry
            </Button>
          ) : null}
          {isFailed ? (
            <Button icon={<EditOutlined />} loading={editRetryTask.isPending} onClick={() => void handleEditRetry()}>
              Edit retry
            </Button>
          ) : null}
          {!isTerminal ? (
            <Popconfirm title="Cancel this task?" onConfirm={() => void handleCancel()}>
              <Button icon={<StopOutlined />} loading={cancelTask.isPending}>
                Cancel task
              </Button>
            </Popconfirm>
          ) : null}
          <Popconfirm title="Delete this task? This cannot be undone." onConfirm={() => void handleDelete()}>
            <Button danger icon={<DeleteOutlined />} loading={deleteTask.isPending}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      </Card>
    </Flex>
  )
}
