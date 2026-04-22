import { ReloadOutlined } from '@ant-design/icons'
import { PageContainer } from '@ant-design/pro-components'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  Alert,
  App,
  Button,
  Card,
  Collapse,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Form,
  Grid,
  Input,
  List,
  Result,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd'

import AIClipWorkflowPanel from '../components/AIClipWorkflowPanel'
import CheckDrawer from '../components/CheckDrawer'
import VersionPanel from '../components/VersionPanel'
import { creativeFlowModeMeta, resolveCreativeFlowMode, resolveCreativeFlowShadowCompare } from '../creativeFlow'
import {
  useCreative,
  usePublishPoolItems,
  usePublishStatus,
  useScheduleConfig,
  useSubmitCreativeComposition,
  useUpdateCreative,
} from '../hooks/useCreatives'
import { useSystemConfig } from '@/hooks/useSystem'
import { useProfiles } from '@/hooks/useProfile'
import { useVideos } from '@/hooks/useVideo'
import { useCopywritings } from '@/hooks/useCopywriting'
import { useCovers } from '@/hooks/useCover'
import { useAudios } from '@/hooks/useAudio'
import { useTopics } from '@/hooks/useTopic'
import {
  creativeStatusMeta,
  creativeReviewConclusionMeta,
  formatCheckConclusion,
  formatCreativeTimestamp,
  formatModeLabel,
  formatRuntimeStatusLabel,
  formatShadowDiffJson,
  formatShadowDiffReasons,
  getShadowDiffFlag,
  getVersionLabel,
  isPoolVersionAligned,
  publishPoolStatusMeta,
  publishRuntimeStatusMeta,
  publishSchedulerModeMeta,
} from '../types/creative'

const { Paragraph, Text } = Typography
const { useBreakpoint } = Grid

type CreativeInputFormValues = {
  title?: string
  profile_id?: number
  video_ids: number[]
  copywriting_ids: number[]
  cover_ids: number[]
  audio_ids: number[]
  topic_ids: number[]
}

export default function CreativeDetail() {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const screens = useBreakpoint()
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const [form] = Form.useForm<CreativeInputFormValues>()
  const creativeId = id ? Number.parseInt(id, 10) : undefined
  const requestedTaskId = Number.parseInt(searchParams.get('taskId') ?? '', 10)
  const prioritizedTaskId = Number.isFinite(requestedTaskId) ? requestedTaskId : undefined
  const detailReturnTo = searchParams.get('returnTo') || '/creative/workbench'
  const taskReturnTo = searchParams.get('returnTo') || (creativeId ? `/creative/${creativeId}` : '/creative/workbench')
  const creativeQuery = useCreative(creativeId)
  const updateCreative = useUpdateCreative(creativeId)
  const submitCreativeComposition = useSubmitCreativeComposition(creativeId)
  const publishStatusQuery = usePublishStatus()
  const scheduleConfigQuery = useScheduleConfig()
  const systemConfigQuery = useSystemConfig()
  const { data: profilesData } = useProfiles()
  const videosQuery = useVideos()
  const copywritingsQuery = useCopywritings()
  const coversQuery = useCovers()
  const audiosQuery = useAudios()
  const topicsQuery = useTopics()
  const activePoolQuery = usePublishPoolItems({
    creativeId,
    status: 'active',
    limit: 50,
    enabled: creativeId !== undefined,
  })
  const invalidatedPoolQuery = usePublishPoolItems({
    creativeId,
    status: 'invalidated',
    limit: 50,
    enabled: creativeId !== undefined,
  })
  const [drawerOpen, setDrawerOpen] = useState(false)
  const selectedProfileId = Form.useWatch('profile_id', form)

  const creative = creativeQuery.data
  const publishStatus = publishStatusQuery.data
  const scheduleConfig = scheduleConfigQuery.data
  const systemConfig = systemConfigQuery.data
  const creativeFlowMode = resolveCreativeFlowMode(systemConfig)
  const creativeFlowShadowCompare = resolveCreativeFlowShadowCompare(systemConfig)
  const creativeFlowMeta = creativeFlowModeMeta[creativeFlowMode]
  const profiles = profilesData?.items ?? []
  const videos = videosQuery.data ?? []
  const copywritings = copywritingsQuery.data ?? []
  const covers = coversQuery.data ?? []
  const audios = audiosQuery.data ?? []
  const topics = topicsQuery.data ?? []
  const inputSnapshot = creative?.input_snapshot ?? {
    profile_id: undefined,
    video_ids: [],
    copywriting_ids: [],
    cover_ids: [],
    audio_ids: [],
    topic_ids: [],
    snapshot_hash: undefined,
  }
  const eligibilityReasons = creative?.eligibility_reasons ?? []
  const currentVersion = creative?.versions?.find((version) => version.is_current) ?? null
  const aiClipOpen = searchParams.get('tool') === 'ai-clip' && Boolean(currentVersion)
  const detailCardMinWidth = screens.md ? 320 : '100%'
  const aiClipDrawerWidth = screens.xl ? 720 : screens.lg ? 640 : screens.md ? 560 : '100vw'

  const openAiClipWorkflow = () => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('tool', 'ai-clip')
    setSearchParams(nextParams, { replace: true })
  }

  const closeAiClipWorkflow = () => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.delete('tool')
    setSearchParams(nextParams, { replace: true })
  }

  const activePoolItems = activePoolQuery.data?.items ?? []
  const invalidatedPoolItems = useMemo(
    () => [...(invalidatedPoolQuery.data?.items ?? [])].sort((left, right) => right.updated_at.localeCompare(left.updated_at)),
    [invalidatedPoolQuery.data?.items],
  )

  const currentPoolItem = useMemo(() => {
    if (!creative?.current_version_id) {
      return activePoolItems[0] ?? null
    }

    return (
      activePoolItems.find((item) => item.creative_version_id === creative.current_version_id)
      ?? activePoolItems[0]
      ?? null
    )
  }, [activePoolItems, creative?.current_version_id])

  const latestInvalidatedPoolItem = invalidatedPoolItems[0] ?? null

  const diagnosticTaskIds = useMemo(() => {
    const ids = new Set<number>()
    if (prioritizedTaskId) {
      ids.add(prioritizedTaskId)
    }
    for (const taskId of creative?.linked_task_ids ?? []) {
      ids.add(taskId)
    }
    if (publishStatus?.current_task_id) {
      ids.add(publishStatus.current_task_id)
    }
    return Array.from(ids)
  }, [creative?.linked_task_ids, prioritizedTaskId, publishStatus?.current_task_id])

  const primaryTaskId = diagnosticTaskIds[0]

  const statusMeta = creative ? creativeStatusMeta[creative.status] : null
  const effectiveCheck = creative?.review_summary?.current_check
  const effectiveCheckMeta = effectiveCheck ? creativeReviewConclusionMeta[effectiveCheck.conclusion] : null

  const schedulerMode = publishStatus?.scheduler_mode ?? scheduleConfig?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatus?.effective_scheduler_mode ?? schedulerMode
  const shadowDiff = publishStatus?.scheduler_shadow_diff
  const currentPublishTaskId = publishStatus?.current_task_id ?? null
  const shadowDiffReasons = formatShadowDiffReasons(shadowDiff)
  const shadowDiffDiffers = getShadowDiffFlag(shadowDiff)
  const diagnosticsUnavailable =
    publishStatusQuery.isError
    || scheduleConfigQuery.isError
    || activePoolQuery.isError
    || invalidatedPoolQuery.isError

  const retryCreative = useCallback(() => {
    void creativeQuery.refetch()
  }, [creativeQuery])

  const retryDiagnostics = useCallback(() => {
    void Promise.all([
      publishStatusQuery.refetch(),
      scheduleConfigQuery.refetch(),
      systemConfigQuery.refetch(),
      activePoolQuery.refetch(),
      invalidatedPoolQuery.refetch(),
    ])
  }, [activePoolQuery, invalidatedPoolQuery, publishStatusQuery, scheduleConfigQuery, systemConfigQuery])

  const openTaskDiagnostics = useCallback((taskId: number) => {
    const params = new URLSearchParams({ returnTo: taskReturnTo })
    navigate(`/task/${taskId}?${params.toString()}`)
  }, [navigate, taskReturnTo])

  useEffect(() => {
    if (!creative) {
      return
    }
    form.setFieldsValue({
      title: creative.title ?? undefined,
      profile_id: inputSnapshot.profile_id ?? undefined,
      video_ids: inputSnapshot.video_ids ?? [],
      copywriting_ids: inputSnapshot.copywriting_ids ?? [],
      cover_ids: inputSnapshot.cover_ids ?? [],
      audio_ids: inputSnapshot.audio_ids ?? [],
      topic_ids: inputSnapshot.topic_ids ?? [],
    })
  }, [creative, form, inputSnapshot])

  const persistCreativeInput = useCallback(async (successMessage?: string) => {
    try {
      const values = await form.validateFields()
      await updateCreative.mutateAsync({
        title: values.title?.trim() ? values.title.trim() : undefined,
        profile_id: values.profile_id ?? null,
        video_ids: values.video_ids ?? [],
        copywriting_ids: values.copywriting_ids ?? [],
        cover_ids: values.cover_ids ?? [],
        audio_ids: values.audio_ids ?? [],
        topic_ids: values.topic_ids ?? [],
      })
      if (successMessage) {
        message.success(successMessage)
      }
      void Promise.all([
        creativeQuery.refetch(),
        activePoolQuery.refetch(),
        invalidatedPoolQuery.refetch(),
      ])
      return true
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) {
        return false
      }
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('保存作品输入失败')
      }
      return false
    }
  }, [activePoolQuery, creativeQuery, form, invalidatedPoolQuery, message, updateCreative])

  const handleSaveInput = useCallback(async () => {
    await persistCreativeInput('作品输入已保存')
  }, [persistCreativeInput])

  const handleSubmitComposition = useCallback(async () => {
    const saved = await persistCreativeInput()
    if (!saved) {
      return
    }

    try {
      const result = await submitCreativeComposition.mutateAsync()
      const nextParams = new URLSearchParams(searchParams)
      nextParams.set('taskId', String(result.task_id))
      nextParams.set('returnTo', taskReturnTo)
      setSearchParams(nextParams, { replace: true })

      const actionMessages: Record<string, string> = {
        created_and_submitted: `已提交合成任务 #${result.task_id}，当前作品会持续同步执行进度`,
        reused_draft_and_submitted: `已复用草稿任务 #${result.task_id} 并提交合成`,
        reused_composing: `已有进行中的合成任务 #${result.task_id}，已直接复用`,
        created_ready_task: `已生成直发版本，作品进入待审核（执行记录 #${result.task_id}）`,
        reused_ready_task: `已复用现有直发结果（执行记录 #${result.task_id}）`,
      }
      message.success(actionMessages[result.submission_action] ?? `操作成功（任务 #${result.task_id}）`)
      void Promise.all([
        creativeQuery.refetch(),
        activePoolQuery.refetch(),
        invalidatedPoolQuery.refetch(),
      ])
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('提交作品合成失败')
      }
    }
  }, [
    activePoolQuery,
    creativeQuery,
    invalidatedPoolQuery,
    message,
    persistCreativeInput,
    searchParams,
    setSearchParams,
    submitCreativeComposition,
    taskReturnTo,
  ])

  const profileOptions = useMemo(
    () => profiles.map((profile) => ({
      value: profile.id,
      label: profile.is_default ? `${profile.name}（默认）` : profile.name,
    })),
    [profiles],
  )
  const videoOptions = useMemo(
    () => videos.map((item) => ({ value: item.id, label: item.name || `视频 #${item.id}` })),
    [videos],
  )
  const copywritingOptions = useMemo(
    () => copywritings.map((item) => ({ value: item.id, label: item.name || `文案 #${item.id}` })),
    [copywritings],
  )
  const coverOptions = useMemo(
    () => covers.map((item) => ({ value: item.id, label: item.name || `封面 #${item.id}` })),
    [covers],
  )
  const audioOptions = useMemo(
    () => audios.map((item) => ({ value: item.id, label: item.name || `音频 #${item.id}` })),
    [audios],
  )
  const topicOptions = useMemo(
    () => topics.map((item) => ({ value: item.id, label: item.name || `话题 #${item.id}` })),
    [topics],
  )
  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === (selectedProfileId ?? inputSnapshot.profile_id)),
    [inputSnapshot.profile_id, profiles, selectedProfileId],
  )
  const submitButtonLabel = activeProfile?.composition_mode === 'none'
    ? '提交直发准备'
    : (currentVersion ? '重新提交合成' : '提交合成')

  const schedulerModeLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : formatModeLabel(schedulerMode)
  const effectiveSchedulerModeLabel = publishStatusQuery.isError
    ? '获取失败'
    : formatModeLabel(effectiveSchedulerMode)
  const runtimeStatusLabel = publishStatusQuery.isError
    ? '获取失败'
    : formatRuntimeStatusLabel(publishStatus?.status)
  const shadowReadLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : (publishStatus?.publish_pool_shadow_read ?? scheduleConfig?.publish_pool_shadow_read)
        ? '开启'
        : '关闭'
  const killSwitchLabel =
    publishStatusQuery.isError && scheduleConfigQuery.isError
      ? '获取失败'
      : (publishStatus?.publish_pool_kill_switch ?? scheduleConfig?.publish_pool_kill_switch)
        ? '开启'
        : '关闭'
  const eligibilityColor =
    creative?.eligibility_status === 'READY_TO_COMPOSE'
      ? 'processing'
      : creative?.eligibility_status === 'INVALID'
        ? 'error'
        : 'default'
  const eligibilityLabel =
    creative?.eligibility_status === 'READY_TO_COMPOSE'
      ? '待提交合成'
      : creative?.eligibility_status === 'INVALID'
        ? '输入无效'
        : '待补输入'

  if (creativeQuery.isLoading && !creative) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (creativeQuery.isError) {
    return (
      <PageContainer title="作品详情" onBack={() => navigate(detailReturnTo)}>
        <div data-testid="creative-detail-error">
          <Result
            status="error"
            title="作品详情暂时无法加载"
            subTitle="当前请求失败，已明确展示为错误状态，不再与空作品或无权限场景混淆。"
            extra={[
              <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={retryCreative}>
                重试加载
              </Button>,
              <Button key="back" onClick={() => navigate(detailReturnTo)}>
                返回工作台
              </Button>,
            ]}
          />
        </div>
      </PageContainer>
    )
  }

  if (!creative || !statusMeta) {
    return (
      <PageContainer title="作品详情" onBack={() => navigate(detailReturnTo)}>
        <Empty
          description="作品不存在，或你没有权限查看这条记录。"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          data-testid="creative-detail-empty"
        />
      </PageContainer>
    )
  }

  const diagnosticsPanels = [
    {
      key: 'publish-runtime',
      label: <span data-testid="creative-diagnostics-publish-trigger">发布运行态</span>,
      children: (
        <Card title="发布与调度诊断" size="small" data-testid="creative-publish-diagnostics">
          {diagnosticsUnavailable ? (
            <Alert
              type="warning"
              showIcon
              message="高级诊断暂不可用"
              description="发布状态、调度配置或发布池数据加载失败，请稍后重试，或转到任务管理继续排查。"
              action={(
                <Button size="small" icon={<ReloadOutlined />} onClick={retryDiagnostics}>
                  重试
                </Button>
              )}
              style={{ marginBottom: 16 }}
            />
          ) : null}
          <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
            <Descriptions.Item label="调度模式">
              <Tag color={publishStatusQuery.isError && scheduleConfigQuery.isError ? 'warning' : schedulerMode ? publishSchedulerModeMeta[schedulerMode].color : 'default'}>
                {schedulerModeLabel}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前生效模式">
              <Tag color={publishStatusQuery.isError ? 'warning' : effectiveSchedulerMode ? publishSchedulerModeMeta[effectiveSchedulerMode].color : 'default'}>
                {effectiveSchedulerModeLabel}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="运行状态">
              <Tag color={publishStatusQuery.isError ? 'warning' : publishStatus?.status ? publishRuntimeStatusMeta[publishStatus.status].color : 'default'}>
                {runtimeStatusLabel}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前任务">
              {currentPublishTaskId !== null ? (
                <Button type="link" onClick={() => openTaskDiagnostics(currentPublishTaskId)}>
                  任务 #{currentPublishTaskId}
                </Button>
              ) : publishStatusQuery.isError ? '获取失败' : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Shadow Read">{shadowReadLabel}</Descriptions.Item>
            <Descriptions.Item label="Kill Switch">{killSwitchLabel}</Descriptions.Item>
            <Descriptions.Item label="当前发布池项">
              {currentPoolItem ? (
                <Space wrap>
                  <Tag color={publishPoolStatusMeta[currentPoolItem.status].color}>{publishPoolStatusMeta[currentPoolItem.status].label}</Tag>
                  <Tag color={isPoolVersionAligned(currentPoolItem) ? 'success' : 'warning'}>版本 #{currentPoolItem.creative_version_id}</Tag>
                </Space>
              ) : activePoolQuery.isError ? '获取失败' : '当前版本暂未进入发布池'}
            </Descriptions.Item>
            <Descriptions.Item label="Pool Item ID">
              {currentPoolItem ? `#${currentPoolItem.id}` : activePoolQuery.isError ? '获取失败' : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="最近失效记录" span={2}>
              {latestInvalidatedPoolItem ? (
                <Space direction="vertical" size={4}>
                  <Text>Pool #{latestInvalidatedPoolItem.id} / 版本 #{latestInvalidatedPoolItem.creative_version_id}</Text>
                  <Text type="secondary">失效于 {formatCreativeTimestamp(latestInvalidatedPoolItem.invalidated_at ?? latestInvalidatedPoolItem.updated_at)}</Text>
                  <Text type="secondary">原因：{latestInvalidatedPoolItem.invalidation_reason ?? '未记录'}</Text>
                </Space>
              ) : invalidatedPoolQuery.isError ? '获取失败' : '暂无失效记录'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      ),
    },
    {
      key: 'publish-pool',
      label: <span data-testid="creative-diagnostics-publish-trigger">发布池历史</span>,
      children: (
        <Card title="发布池记录" size="small" data-testid="creative-publish-pool-card">
          {activePoolQuery.isError || invalidatedPoolQuery.isError ? (
            <Alert
              type="warning"
              showIcon
              message="发布池历史暂时不可用"
              description="当前不能把发布池请求失败误判为没有历史记录，请稍后重试。"
              action={(
                <Button size="small" icon={<ReloadOutlined />} onClick={retryDiagnostics}>
                  重试
                </Button>
              )}
            />
          ) : activePoolItems.length === 0 && invalidatedPoolItems.length === 0 ? (
            <Empty description="当前没有发布池记录" />
          ) : (
            <List
              dataSource={[...activePoolItems, ...invalidatedPoolItems]}
              renderItem={(item) => {
                const aligned = isPoolVersionAligned(item)
                return (
                  <List.Item key={`${item.status}-${item.id}`} data-testid={`creative-pool-item-${item.id}`}>
                    <Space direction="vertical" size={6} style={{ width: '100%' }}>
                      <Space wrap>
                        <Tag color={publishPoolStatusMeta[item.status].color}>{publishPoolStatusMeta[item.status].label}</Tag>
                        <Tag color={aligned ? 'success' : 'warning'}>版本 #{item.creative_version_id}</Tag>
                        <Tag color={aligned ? 'success' : 'warning'}>{aligned ? '版本已对齐' : '版本存在偏差'}</Tag>
                        <Tag>Pool #{item.id}</Tag>
                      </Space>
                      <Text type="secondary">入池于 {formatCreativeTimestamp(item.created_at)}，最近更新时间 {formatCreativeTimestamp(item.updated_at)}</Text>
                      {item.invalidation_reason ? <Text type="secondary">失效原因：{item.invalidation_reason}</Text> : null}
                    </Space>
                  </List.Item>
                )
              }}
            />
          )}
        </Card>
      ),
    },
  ]

  if (shadowDiff) {
    diagnosticsPanels.push({
      key: 'cutover-shadow-diff',
      label: <span data-testid="creative-diagnostics-cutover-trigger">Cutover 差异</span>,
      children: (
        <Card title="Cutover 对账" size="small" data-testid="creative-shadow-diff">
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Space wrap>
              <Tag color={shadowDiffDiffers ? 'warning' : 'success'}>{shadowDiffDiffers ? '存在差异' : '已对齐'}</Tag>
              {shadowDiffReasons.length > 0
                ? shadowDiffReasons.map((reason) => <Tag key={reason}>{reason}</Tag>)
                : <Tag>无差异原因</Tag>}
            </Space>
            <pre style={{ margin: 0, padding: 12, background: '#fafafa', borderRadius: 8, overflow: 'auto' }}>{formatShadowDiffJson(shadowDiff)}</pre>
          </Space>
        </Card>
      ),
    })
  }

  return (
    <PageContainer
      title={creative.title ?? creative.creative_no}
      subTitle={creative.creative_no}
      onBack={() => navigate(detailReturnTo)}
      extra={[
        primaryTaskId ? (
          <Button key="task-detail" onClick={() => openTaskDiagnostics(primaryTaskId)} data-testid="creative-open-task-diagnostics">
            查看执行记录
          </Button>
        ) : null,
        currentVersion ? (
          <Button key="ai-clip" onClick={openAiClipWorkflow} data-testid="creative-open-ai-clip">
            AIClip 工作流
          </Button>
        ) : null,
        currentVersion ? (
          <Button key="review" type="primary" data-testid="creative-open-review" onClick={() => setDrawerOpen(true)}>
            审核当前版本
          </Button>
        ) : null,
      ].filter(Boolean)}
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        {creative.generation_error_msg ? (
          <Alert
            type="warning"
            showIcon
            message="当前生成链路存在失败记录"
            description={`最近失败于 ${formatCreativeTimestamp(creative.generation_failed_at)}，错误：${creative.generation_error_msg}`}
          />
        ) : null}

        <Card title="业务概览">
          <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
            <Descriptions.Item label="作品编号">{creative.creative_no}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusMeta.color}>{statusMeta.label}</Tag></Descriptions.Item>
            <Descriptions.Item label="入口模式">
              <Space wrap>
                <Tag>{creativeFlowMeta.label}</Tag>
                <Tag>{creativeFlowShadowCompare ? 'Shadow Compare：开启' : 'Shadow Compare：关闭'}</Tag>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="合成准备"><Tag color={eligibilityColor}>{eligibilityLabel}</Tag></Descriptions.Item>
            <Descriptions.Item label="当前版本 ID">{creative.current_version_id ?? '-'}</Descriptions.Item>
            <Descriptions.Item label="最近更新时间">{formatCreativeTimestamp(creative.updated_at)}</Descriptions.Item>
          </Descriptions>
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            这里先维护作品输入与业务判断，再决定是否发起合成；任务、发布链路与 Cutover 诊断继续作为辅助入口保留。
          </Paragraph>
        </Card>

        <Card
          title="作品输入"
          extra={(
            <Space>
              <Text type="secondary">Snapshot Hash：{inputSnapshot.snapshot_hash ?? '-'}</Text>
              <Button type="primary" loading={updateCreative.isPending} onClick={() => void handleSaveInput()}>
                保存作品输入
              </Button>
              <Button
                type="primary"
                ghost
                loading={submitCreativeComposition.isPending}
                disabled={creative.eligibility_status !== 'READY_TO_COMPOSE' || updateCreative.isPending}
                onClick={() => void handleSubmitComposition()}
                data-testid="creative-submit-composition"
              >
                {submitButtonLabel}
              </Button>
            </Space>
          )}
        >
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <Form form={form} layout="vertical">
              <Form.Item name="title" label="作品标题">
                <Input placeholder="给这条作品起一个便于检索和协作的名字" allowClear />
              </Form.Item>

              <Form.Item name="profile_id" label="合成配置">
                <Select
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  placeholder="选择合成配置"
                  options={profileOptions}
                />
              </Form.Item>

              <Form.Item
                name="video_ids"
                label="视频素材"
                rules={[{ required: true, type: 'array', min: 1, message: '至少选择 1 个视频' }]}
              >
                <Select
                  mode="multiple"
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  placeholder="选择视频素材"
                  options={videoOptions}
                  loading={videosQuery.isLoading}
                />
              </Form.Item>

              <Form.Item name="copywriting_ids" label="文案素材">
                <Select
                  mode="multiple"
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  placeholder="可选：选择文案素材"
                  options={copywritingOptions}
                  loading={copywritingsQuery.isLoading}
                />
              </Form.Item>

              <Form.Item name="cover_ids" label="封面素材">
                <Select
                  mode="multiple"
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  placeholder="可选：选择封面素材"
                  options={coverOptions}
                  loading={coversQuery.isLoading}
                />
              </Form.Item>

              <Form.Item name="audio_ids" label="音频素材">
                <Select
                  mode="multiple"
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  placeholder="可选：选择音频素材"
                  options={audioOptions}
                  loading={audiosQuery.isLoading}
                />
              </Form.Item>

              <Form.Item name="topic_ids" label="话题">
                <Select
                  mode="multiple"
                  allowClear
                  showSearch
                  optionFilterProp="label"
                  placeholder="可选：选择话题"
                  options={topicOptions}
                  loading={topicsQuery.isLoading}
                />
              </Form.Item>
            </Form>

            <Alert
              type={creative.eligibility_status === 'INVALID' ? 'warning' : creative.eligibility_status === 'READY_TO_COMPOSE' ? 'success' : 'info'}
              showIcon
              message={
                creative.eligibility_status === 'READY_TO_COMPOSE'
                  ? '当前作品已满足提交合成条件'
                  : creative.eligibility_status === 'INVALID'
                    ? '当前作品输入存在无效项'
                    : '当前作品仍待补齐输入'
              }
              description={
                eligibilityReasons.length > 0 ? (
                  <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                    {eligibilityReasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                ) : '当前输入已满足最小前置条件，可继续进入合成执行链。'
              }
            />
          </Space>
        </Card>

        <Flex gap={16} wrap="wrap" align="stretch">
          <Card title="当前版本" style={{ flex: 1, minWidth: detailCardMinWidth }}>
            {creative.current_version ? (
              <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
                <Descriptions.Item label="版本 ID">{creative.current_version.id}</Descriptions.Item>
                <Descriptions.Item label="版本号">{getVersionLabel(creative.current_version.version_no)}</Descriptions.Item>
                <Descriptions.Item label="版本标题" span={2}>{creative.current_version.title ?? '未命名版本'}</Descriptions.Item>
                <Descriptions.Item label="父版本 ID">{creative.current_version.parent_version_id ?? '-'}</Descriptions.Item>
                <Descriptions.Item label="PackageRecord ID">{creative.current_version.package_record_id ?? '-'}</Descriptions.Item>
              </Descriptions>
            ) : <Empty description="当前还没有可用版本" />}
          </Card>

          <Card title="当前有效审核结论" style={{ flex: 1, minWidth: 320 }} data-testid="creative-review-summary">
            {effectiveCheck && effectiveCheckMeta ? (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Space wrap>
                  <Tag color={effectiveCheckMeta.color}>{formatCheckConclusion(effectiveCheck)}</Tag>
                  <Tag color="processing">版本 {getVersionLabel(creative.review_summary?.current_version_id)}</Tag>
                </Space>
                <Text type="secondary">最近审核于 {formatCreativeTimestamp(effectiveCheck.updated_at)}</Text>
                {effectiveCheck.note ? (
                  <Paragraph style={{ marginBottom: 0 }}>{effectiveCheck.note}</Paragraph>
                ) : (
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>未填写审核备注</Paragraph>
                )}
                {creative.review_summary?.total_checks ? (
                  <Text type="secondary">累计审核记录 {creative.review_summary.total_checks} 条</Text>
                ) : null}
              </Space>
            ) : (
              <Alert
                type="info"
                showIcon
                message="当前版本还没有有效审核结论"
                description="你可以先发起一次审核；历史版本的旧结论仍保留在下方版本时间线中。"
              />
            )}
          </Card>
        </Flex>

        <VersionPanel
          versions={creative.versions ?? []}
          reviewSummary={creative.review_summary}
          onOpenAiClipWorkflow={(version) => {
            if (version.is_current) {
              openAiClipWorkflow()
            }
          }}
          onReviewVersion={(version) => {
            if (version.is_current) {
              setDrawerOpen(true)
            }
          }}
        />

        <Card title="执行记录">
          {diagnosticTaskIds.length > 0 ? (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                任务管理只承接执行进度、失败重试与排障细节；作品详情仍是当前创作输入与状态判断的主视图。
              </Paragraph>
              <Space wrap>
                {diagnosticTaskIds.map((taskId) => (
                  <Button key={taskId} onClick={() => openTaskDiagnostics(taskId)} data-testid={`creative-open-task-${taskId}`}>
                    执行记录 #{taskId}
                  </Button>
                ))}
                <Button onClick={() => navigate('/task/list')}>打开任务管理</Button>
              </Space>
            </Space>
          ) : (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                这条作品还没有关联执行记录。先保存作品输入，达到“待提交合成”后，可直接在本页提交合成或生成直发准备。
              </Paragraph>
              <Space wrap>
                <Button
                  type="primary"
                  ghost
                  disabled={creative.eligibility_status !== 'READY_TO_COMPOSE'}
                  loading={submitCreativeComposition.isPending}
                  onClick={() => void handleSubmitComposition()}
                >
                  {submitButtonLabel}
                </Button>
                <Button onClick={() => navigate('/task/list')}>打开任务管理</Button>
              </Space>
            </Space>
          )}
        </Card>

        <Card title="高级诊断" extra={<Text type="secondary">展开查看发布池 / 调度 / Cutover 差异</Text>}>
          <Paragraph type="secondary">
            以下信息用于排查发布池、调度切换与 Cutover 问题；只有在需要定位异常时再展开查看。
          </Paragraph>
          <Collapse items={diagnosticsPanels} />
        </Card>
      </Space>

      <CheckDrawer creativeId={creativeId} open={drawerOpen} version={currentVersion} onClose={() => setDrawerOpen(false)} />

      <Drawer title="AIClip 工作流" open={aiClipOpen} width={aiClipDrawerWidth} onClose={closeAiClipWorkflow} destroyOnClose styles={{ body: { padding: screens.md ? 24 : 16 } }}>
        <div data-testid="creative-ai-clip-drawer">
          <AIClipWorkflowPanel
            creativeContext={creativeId && currentVersion ? {
              creativeId,
              creativeTitle: creative.title,
              sourceVersionId: currentVersion.id,
              sourceVersionLabel: getVersionLabel(currentVersion.version_no),
              onSubmitted: () => { closeAiClipWorkflow() },
            } : null}
          />
        </div>
      </Drawer>
    </PageContainer>
  )
}
