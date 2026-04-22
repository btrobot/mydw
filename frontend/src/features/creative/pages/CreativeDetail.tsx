import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { PageContainer } from '@ant-design/pro-components'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  Alert,
  App,
  Button,
  Card,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Form,
  Grid,
  Input,
  InputNumber,
  List,
  Result,
  Select,
  Space,
  Spin,
  Switch,
  Tag,
  Typography,
} from 'antd'

import AIClipWorkflowPanel from '../components/AIClipWorkflowPanel'
import CheckDrawer from '../components/CheckDrawer'
import VersionPanel from '../components/VersionPanel'
import { creativeFlowModeMeta, resolveCreativeFlowMode, resolveCreativeFlowShadowCompare } from '../creativeFlow'
import {
  buildCreativeAuthoringPayload,
  countEnabledCreativeInputItems,
  creativeInputMaterialMeta,
  formatCreativeDuration,
  toCreativeAuthoringFormValues,
  type CreativeAuthoringFormValues,
  type CreativeInputMaterialType,
} from '../creativeAuthoring'
import {
  useCreative,
  usePublishPoolItems,
  usePublishStatus,
  useScheduleConfig,
  useSubmitCreativeComposition,
  useUpdateCreative,
} from '../hooks/useCreatives'
import { useProducts } from '@/hooks/useProduct'
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

type CreativeDetailDiagnosticsView = 'advanced'

export default function CreativeDetail() {
  const location = useLocation()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const screens = useBreakpoint()
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const [form] = Form.useForm<CreativeAuthoringFormValues>()
  const creativeId = id ? Number.parseInt(id, 10) : undefined
  const requestedTaskId = Number.parseInt(searchParams.get('taskId') ?? '', 10)
  const prioritizedTaskId = Number.isFinite(requestedTaskId) ? requestedTaskId : undefined
  const detailCurrentRoute = useMemo(() => {
    const currentPath = `${location.pathname}${location.search}`
    return currentPath || (creativeId ? `/creative/${creativeId}` : '/creative/workbench')
  }, [creativeId, location.pathname, location.search])
  const detailReturnTo = searchParams.get('returnTo') || '/creative/workbench'
  const taskReturnTo = searchParams.get('returnTo') || detailCurrentRoute
  const creativeQuery = useCreative(creativeId)
  const updateCreative = useUpdateCreative(creativeId)
  const submitCreativeComposition = useSubmitCreativeComposition(creativeId)
  const publishStatusQuery = usePublishStatus()
  const scheduleConfigQuery = useScheduleConfig()
  const systemConfigQuery = useSystemConfig()
  const productsQuery = useProducts()
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
  const watchedSubjectProductName = Form.useWatch('subject_product_name_snapshot', form)
  const watchedTargetDuration = Form.useWatch('target_duration_seconds', form)
  const authoredInputItems = Form.useWatch('input_items', form) ?? []
  const detailDiagnosticsOpen = searchParams.get('diagnostics') === 'advanced'

  const creative = creativeQuery.data
  const publishStatus = publishStatusQuery.data
  const scheduleConfig = scheduleConfigQuery.data
  const systemConfig = systemConfigQuery.data
  const creativeFlowMode = resolveCreativeFlowMode(systemConfig)
  const creativeFlowShadowCompare = resolveCreativeFlowShadowCompare(systemConfig)
  const creativeFlowMeta = creativeFlowModeMeta[creativeFlowMode]
  const profiles = profilesData?.items ?? []
  const products = productsQuery.data ?? []
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

  const setDiagnosticsView = useCallback((diagnostics?: CreativeDetailDiagnosticsView) => {
    const nextParams = new URLSearchParams(searchParams)
    if (diagnostics) {
      nextParams.set('diagnostics', diagnostics)
    } else {
      nextParams.delete('diagnostics')
    }
    setSearchParams(nextParams, { replace: true })
  }, [searchParams, setSearchParams])

  const handleOpenDiagnostics = useCallback(() => {
    setDiagnosticsView('advanced')
  }, [setDiagnosticsView])

  const handleCloseDiagnostics = useCallback(() => {
    setDiagnosticsView(undefined)
  }, [setDiagnosticsView])

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
    form.setFieldsValue(toCreativeAuthoringFormValues(creative))
  }, [creative, form])

  const persistCreativeInput = useCallback(async (successMessage?: string) => {
    try {
      const values = await form.validateFields()
      await updateCreative.mutateAsync(buildCreativeAuthoringPayload(values))
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
  const productOptions = useMemo(
    () => products.map((product) => ({ value: product.id, label: product.name })),
    [products],
  )
  const productNameById = useMemo(
    () => new Map(products.map((product) => [product.id, product.name])),
    [products],
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
  const materialTypeOptions = useMemo(
    () => Object.entries(creativeInputMaterialMeta).map(([value, meta]) => ({
      value,
      label: meta.label,
    })),
    [],
  )
  const materialOptionsByType = useMemo<Record<CreativeInputMaterialType, Array<{ value: number; label: string }>>>(
    () => ({
      video: videoOptions,
      copywriting: copywritingOptions,
      cover: coverOptions,
      audio: audioOptions,
      topic: topicOptions,
    }),
    [audioOptions, copywritingOptions, coverOptions, topicOptions, videoOptions],
  )
  const materialLoadingByType = useMemo<Record<CreativeInputMaterialType, boolean>>(
    () => ({
      video: videosQuery.isLoading,
      copywriting: copywritingsQuery.isLoading,
      cover: coversQuery.isLoading,
      audio: audiosQuery.isLoading,
      topic: topicsQuery.isLoading,
    }),
    [
      audiosQuery.isLoading,
      copywritingsQuery.isLoading,
      coversQuery.isLoading,
      topicsQuery.isLoading,
      videosQuery.isLoading,
    ],
  )
  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === (selectedProfileId ?? inputSnapshot.profile_id)),
    [inputSnapshot.profile_id, profiles, selectedProfileId],
  )
  const activeInputItemCount = countEnabledCreativeInputItems(authoredInputItems)
  const handleSubjectProductChange = useCallback((productId?: number) => {
    if (!productId) {
      return
    }
    const nextName = productNameById.get(productId)
    if (nextName) {
      form.setFieldValue('subject_product_name_snapshot', nextName)
    }
  }, [form, productNameById])
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
      <Flex justify="center" style={{ padding: 48 }} data-testid="creative-detail-loading">
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
            subTitle="详情加载失败，当前无法继续查看输入、版本或审核信息。"
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

  return (
    <PageContainer
      title={creative.title ?? creative.creative_no}
      subTitle={creative.creative_no}
      onBack={() => navigate(detailReturnTo)}
      extra={[
        <Button key="advanced-diagnostics" onClick={handleOpenDiagnostics} data-testid="creative-open-advanced-diagnostics">
          查看高级诊断
        </Button>,
        currentVersion ? (
          <Button key="ai-clip" onClick={openAiClipWorkflow} data-testid="creative-open-ai-clip">
            进入 AIClip
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

        {diagnosticsUnavailable ? (
          <Alert
            type="warning"
            showIcon
            message="部分高级诊断暂不可用，可通过“查看高级诊断”重试。"
            data-testid="creative-detail-diagnostics-notice"
          />
        ) : null}

        <Card title="业务概览">
          <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
            <Descriptions.Item label="作品编号">{creative.creative_no}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusMeta.color}>{statusMeta.label}</Tag></Descriptions.Item>
            <Descriptions.Item label="合成准备"><Tag color={eligibilityColor}>{eligibilityLabel}</Tag></Descriptions.Item>
            <Descriptions.Item label="当前版本 ID">{creative.current_version_id ?? '-'}</Descriptions.Item>
            <Descriptions.Item label="最近更新时间">{formatCreativeTimestamp(creative.updated_at)}</Descriptions.Item>
          </Descriptions>
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            默认先处理作品输入、版本与审核；任务与发布侧信息请从“查看高级诊断”进入。
          </Paragraph>
        </Card>

        <Card
          title="创作 brief 与素材编排"
          extra={(
            <Space wrap>
              <Text type="secondary">编排项：{activeInputItemCount}</Text>
              <Text type="secondary">兼容 Snapshot Hash：{inputSnapshot.snapshot_hash ?? '-'}</Text>
              <Button
                loading={updateCreative.isPending}
                onClick={() => void handleSaveInput()}
                data-testid="creative-detail-save-authoring"
              >
                保存创作定义
              </Button>
              <Button
                type="primary"
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
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              这里维护作品级业务定义：商品、主文案、目标时长，以及 input_items 编排顺序。旧版列表字段仅保留为兼容投影与快照。
            </Paragraph>

            <Descriptions bordered size="small" column={screens.lg ? 4 : screens.md ? 2 : 1}>
              <Descriptions.Item label="主体商品">
                {watchedSubjectProductName || creative.subject_product_name_snapshot || '待补充'}
              </Descriptions.Item>
              <Descriptions.Item label="目标时长">
                {formatCreativeDuration(watchedTargetDuration ?? creative.target_duration_seconds)}
              </Descriptions.Item>
              <Descriptions.Item label="启用编排项">{activeInputItemCount}</Descriptions.Item>
              <Descriptions.Item label="合成配置">
                {activeProfile?.name ?? (inputSnapshot.profile_id ? `配置 #${inputSnapshot.profile_id}` : '待选择')}
              </Descriptions.Item>
            </Descriptions>

            <Form form={form} layout="vertical">
              <Flex gap={16} wrap="wrap" align="start">
                <Form.Item name="title" label="作品标题" style={{ flex: 1, minWidth: 260 }}>
                  <Input placeholder="给这条作品起一个便于检索和协作的名字" allowClear />
                </Form.Item>

                <Form.Item name="profile_id" label="合成配置" style={{ flex: 1, minWidth: 220 }}>
                  <Select
                    allowClear
                    showSearch
                    optionFilterProp="label"
                    placeholder="选择合成配置"
                    options={profileOptions}
                  />
                </Form.Item>
              </Flex>

              <Flex gap={16} wrap="wrap" align="start">
                <Form.Item name="subject_product_id" label="主体商品" style={{ flex: 1, minWidth: 220 }}>
                  <Select
                    allowClear
                    showSearch
                    optionFilterProp="label"
                    placeholder="选择主体商品"
                    options={productOptions}
                    loading={productsQuery.isLoading}
                    onChange={(value) => handleSubjectProductChange(value)}
                    data-testid="creative-detail-subject-product"
                  />
                </Form.Item>

                <Form.Item
                  name="subject_product_name_snapshot"
                  label="商品名称快照"
                  style={{ flex: 1, minWidth: 260 }}
                >
                  <Input
                    placeholder="用于作品 brief / 版本沉淀的商品名称"
                    allowClear
                    data-testid="creative-detail-product-snapshot"
                  />
                </Form.Item>

                <Form.Item
                  name="target_duration_seconds"
                  label="目标时长（秒）"
                  style={{ width: screens.md ? 180 : '100%' }}
                >
                  <InputNumber
                    min={1}
                    precision={0}
                    style={{ width: '100%' }}
                    placeholder="例如 30"
                    data-testid="creative-detail-target-duration"
                  />
                </Form.Item>
              </Flex>

              <Form.Item name="main_copywriting_text" label="主文案">
                <Input.TextArea
                  autoSize={{ minRows: 3, maxRows: 6 }}
                  placeholder="填写作品级主文案；它属于作品 brief，而不是单个素材条目。"
                  data-testid="creative-detail-main-copywriting"
                />
              </Form.Item>

              <Form.List name="input_items">
                {(fields, { add, move, remove }) => (
                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Flex justify="space-between" align="center" wrap="wrap" gap={12}>
                      <Space direction="vertical" size={0}>
                        <Text strong>素材编排（input_items）</Text>
                        <Text type="secondary">支持显式排序、重复添加同一素材，以及为单项补充角色 / 时长 / 裁切信息。</Text>
                      </Space>
                      <Button
                        type="dashed"
                        icon={<PlusOutlined />}
                        onClick={() => add({ material_type: 'video', enabled: true })}
                        data-testid="creative-detail-add-input-item"
                      >
                        添加编排项
                      </Button>
                    </Flex>

                    {fields.length === 0 ? (
                      <Alert
                        type="info"
                        showIcon
                        message="当前还没有编排项"
                        description="请至少添加 1 条素材编排；如果需要重复使用同一条素材，可以重复添加。"
                      />
                    ) : null}

                    {fields.map((field, index) => {
                      const materialType =
                        (form.getFieldValue(['input_items', field.name, 'material_type']) as CreativeInputMaterialType | undefined)
                        ?? 'video'
                      const materialOptions = materialOptionsByType[materialType] ?? []

                      return (
                        <Card
                          key={field.key}
                          type="inner"
                          size="small"
                          title={`编排项 ${index + 1}`}
                          extra={(
                            <Space>
                              <Button
                                size="small"
                                icon={<ArrowUpOutlined />}
                                disabled={index === 0}
                                onClick={() => move(index, index - 1)}
                              >
                                上移
                              </Button>
                              <Button
                                size="small"
                                icon={<ArrowDownOutlined />}
                                disabled={index === fields.length - 1}
                                onClick={() => move(index, index + 1)}
                              >
                                下移
                              </Button>
                              <Button
                                size="small"
                                danger
                                icon={<DeleteOutlined />}
                                onClick={() => remove(field.name)}
                              >
                                删除
                              </Button>
                            </Space>
                          )}
                        >
                          <Flex gap={16} wrap="wrap" align="start">
                            <Form.Item
                              name={[field.name, 'material_type']}
                              label="素材类型"
                              rules={[{ required: true, message: '请选择素材类型' }]}
                              style={{ minWidth: 160, flex: 1 }}
                            >
                              <Select
                                options={materialTypeOptions}
                                data-testid={`creative-detail-input-item-type-${index}`}
                              />
                            </Form.Item>

                            <Form.Item
                              name={[field.name, 'material_id']}
                              label={creativeInputMaterialMeta[materialType].label}
                              rules={[{ required: true, message: '请选择素材' }]}
                              style={{ minWidth: 220, flex: 1.4 }}
                            >
                              <Select
                                allowClear
                                showSearch
                                optionFilterProp="label"
                                placeholder={`选择${creativeInputMaterialMeta[materialType].label}`}
                                options={materialOptions}
                                loading={materialLoadingByType[materialType]}
                                data-testid={`creative-detail-input-item-material-${index}`}
                              />
                            </Form.Item>

                            <Form.Item name={[field.name, 'role']} label="用途 / 角色" style={{ minWidth: 180, flex: 1 }}>
                              <Input placeholder="例如 开场 / 主镜头 / CTA / 封面" allowClear />
                            </Form.Item>

                            <Form.Item
                              name={[field.name, 'slot_duration_seconds']}
                              label="槽位时长（秒）"
                              style={{ width: 160 }}
                            >
                              <InputNumber min={1} precision={0} style={{ width: '100%' }} />
                            </Form.Item>

                            <Form.Item name={[field.name, 'trim_in']} label="裁切起点（秒）" style={{ width: 160 }}>
                              <InputNumber min={0} style={{ width: '100%' }} />
                            </Form.Item>

                            <Form.Item name={[field.name, 'trim_out']} label="裁切终点（秒）" style={{ width: 160 }}>
                              <InputNumber min={0} style={{ width: '100%' }} />
                            </Form.Item>

                            <Form.Item
                              name={[field.name, 'enabled']}
                              label="启用"
                              valuePropName="checked"
                              style={{ width: 120 }}
                            >
                              <Switch checkedChildren="启用" unCheckedChildren="停用" />
                            </Form.Item>
                          </Flex>
                        </Card>
                      )
                    })}
                  </Space>
                )}
              </Form.List>
            </Form>

            <Alert
              type={creative.eligibility_status === 'INVALID' ? 'warning' : creative.eligibility_status === 'READY_TO_COMPOSE' ? 'success' : 'info'}
              showIcon
              message={
                creative.eligibility_status === 'READY_TO_COMPOSE'
                  ? '当前作品已满足提交合成条件'
                  : creative.eligibility_status === 'INVALID'
                    ? '当前作品输入存在无效项'
                    : '当前作品仍待补齐创作定义'
              }
              description={
                eligibilityReasons.length > 0 ? (
                  <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                    {eligibilityReasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                ) : '当前作品已具备最小创作 brief 与编排条件，可继续进入合成执行链。'
              }
            />
          </Space>
        </Card>

        <Flex gap={16} wrap="wrap" align="stretch">
          <Card title="当前版本结果" style={{ flex: 1, minWidth: detailCardMinWidth }}>
            {creative.current_version ? (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
                  <Descriptions.Item label="版本 ID">{creative.current_version.id}</Descriptions.Item>
                  <Descriptions.Item label="版本号">{getVersionLabel(creative.current_version.version_no)}</Descriptions.Item>
                  <Descriptions.Item label="版本标题" span={2}>{creative.current_version.title ?? '未命名版本'}</Descriptions.Item>
                  <Descriptions.Item label="父版本 ID">{creative.current_version.parent_version_id ?? '-'}</Descriptions.Item>
                  <Descriptions.Item label="发布侧 PackageRecord">{creative.current_version.package_record_id ?? '-'}</Descriptions.Item>
                </Descriptions>
                <Paragraph type="secondary" style={{ marginBottom: 0 }} data-testid="creative-current-version-semantics">
                  版本结果承接当前作品 brief 与素材编排；它是审核对象，发布侧候选与执行任务请在高级诊断查看。
                </Paragraph>
              </Space>
            ) : <Empty description="当前还没有可用版本结果" />}
          </Card>

          <Card title="当前有效审核结论" style={{ flex: 1, minWidth: 320 }} data-testid="creative-review-summary">
            {effectiveCheck && effectiveCheckMeta ? (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0 }} data-testid="creative-review-summary-semantics">
                  审核结论只判断当前版本结果是否可继续进入发布承接，不改写作品定义本身。
                </Paragraph>
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
                message="当前版本结果待审核"
                description="请先审核当前版本结果；历史版本记录保留在下方时间线中。"
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

      </Space>

      <Drawer
        title="高级诊断（任务 / 发布侧）"
        open={detailDiagnosticsOpen}
        width={screens.xl ? 720 : screens.lg ? 640 : screens.md ? 560 : '100vw'}
        onClose={handleCloseDiagnostics}
        destroyOnClose
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }} data-testid="creative-detail-diagnostics-drawer">
          <Card title="执行任务诊断" size="small" data-testid="creative-task-diagnostics-card">
            {diagnosticTaskIds.length > 0 ? (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0 }} data-testid="creative-task-diagnostics-note">
                  任务管理只承接执行进度、失败重试与排障，不回写作品定义、版本结果或发布侧承接语义。
                </Paragraph>
                <Space wrap>
                  {primaryTaskId ? (
                    <Button
                      type="primary"
                      onClick={() => openTaskDiagnostics(primaryTaskId)}
                      data-testid="creative-open-task-diagnostics"
                    >
                      查看主执行诊断
                    </Button>
                  ) : null}
                  {diagnosticTaskIds.map((taskId) => (
                    <Button key={taskId} onClick={() => openTaskDiagnostics(taskId)} data-testid={`creative-open-task-${taskId}`}>
                      执行诊断 #{taskId}
                    </Button>
                  ))}
                  <Button onClick={() => navigate('/task/list')}>打开任务管理</Button>
                </Space>
              </Space>
            ) : (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  这条作品还没有关联执行记录；如需排查执行侧信息，可从这里进入任务管理。
                </Paragraph>
                <Button onClick={() => navigate('/task/list')}>打开任务管理</Button>
              </Space>
            )}
          </Card>

          <Card title="发布侧能力与调度诊断" size="small" data-testid="creative-publish-diagnostics">
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
            <Paragraph type="secondary" style={{ marginBottom: 16 }} data-testid="creative-publish-semantics">
              这里查看发布侧候选项、调度模式与 cutover 对账；如果当前作品定义暂不能直达发布，表示当前执行引擎能力尚未覆盖，并不代表作品定义无效。
            </Paragraph>
            <Descriptions bordered size="small" column={screens.md ? 2 : 1}>
              <Descriptions.Item label="入口模式">
                <Space wrap>
                  <Tag>{creativeFlowMeta.label}</Tag>
                  <Tag>{creativeFlowShadowCompare ? 'Shadow Compare：开启' : 'Shadow Compare：关闭'}</Tag>
                </Space>
              </Descriptions.Item>
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
              <Descriptions.Item label="当前发布执行任务">
                {currentPublishTaskId !== null ? (
                  <Button type="link" onClick={() => openTaskDiagnostics(currentPublishTaskId)}>
                    任务 #{currentPublishTaskId}
                  </Button>
                ) : publishStatusQuery.isError ? '获取失败' : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Shadow Read">{shadowReadLabel}</Descriptions.Item>
              <Descriptions.Item label="Kill Switch">{killSwitchLabel}</Descriptions.Item>
              <Descriptions.Item label="当前发布侧候选项">
                {currentPoolItem ? (
                  <Space wrap>
                    <Tag color={publishPoolStatusMeta[currentPoolItem.status].color}>{publishPoolStatusMeta[currentPoolItem.status].label}</Tag>
                    <Tag color={isPoolVersionAligned(currentPoolItem) ? 'success' : 'warning'}>版本 #{currentPoolItem.creative_version_id}</Tag>
                  </Space>
                ) : activePoolQuery.isError ? '获取失败' : '当前版本尚未生成发布侧候选项'}
              </Descriptions.Item>
              <Descriptions.Item label="候选项 ID">
                {currentPoolItem ? `#${currentPoolItem.id}` : activePoolQuery.isError ? '获取失败' : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="最近候选失效记录" span={2}>
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

          <Card title="发布侧候选记录" size="small" data-testid="creative-publish-pool-card">
            <Paragraph type="secondary" style={{ marginBottom: 16 }} data-testid="creative-publish-pool-semantics">
              这些记录描述发布侧候选与失效历史；若出现不对齐，说明当前发布承接仍受能力边界约束。
            </Paragraph>
            {activePoolQuery.isError || invalidatedPoolQuery.isError ? (
              <Alert
                type="warning"
                showIcon
                message="发布池历史暂时不可用"
                description="发布池请求失败，请稍后重试。"
                action={(
                  <Button size="small" icon={<ReloadOutlined />} onClick={retryDiagnostics}>
                    重试
                  </Button>
                )}
              />
            ) : activePoolItems.length === 0 && invalidatedPoolItems.length === 0 ? (
              <Empty description="当前没有发布侧候选记录" />
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
                          <Tag color={aligned ? 'success' : 'warning'}>{aligned ? '发布侧已对齐' : '发布侧存在偏差'}</Tag>
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

          {shadowDiff ? (
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
          ) : null}
        </Space>
      </Drawer>

      <CheckDrawer creativeId={creativeId} open={drawerOpen} version={currentVersion} onClose={() => setDrawerOpen(false)} />

      <Drawer title="AIClip" open={aiClipOpen} width={aiClipDrawerWidth} onClose={closeAiClipWorkflow} destroyOnClose styles={{ body: { padding: screens.md ? 24 : 16 } }}>
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
