import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { PageContainer, ProDescriptions } from '@ant-design/pro-components'
import { useCallback, useMemo } from 'react'
import {
  Alert,
  App,
  Button,
  Card,
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
import {
  CreativeCurrentSelectionSection,
  CreativeDetailHeroCard,
  CreativeSourceZoneSection,
} from '../components/detail/CreativeDetailProjection'
import { buildCreativeDetailProjectionModel } from '../components/detail/projection'
import DiagnosticsActionPanel, { type DiagnosticsRecommendation } from '../components/diagnostics/DiagnosticsActionPanel'
import VersionPanel from '../components/VersionPanel'
import {
  creativeCandidateMeta,
  creativeSelectedMediaMeta,
  formatCreativeDuration,
  type CreativeAuthoringCandidateType,
  type CreativeSelectedMediaType,
} from '../creativeAuthoring'
import { useCreative } from '../hooks/useCreatives'
import {
  creativeStatusMeta,
  formatCheckConclusion,
  formatCreativeDurationSeconds,
  formatCreativeText,
  formatCreativeTimestamp,
  formatShadowDiffJson,
  getVersionLabel,
  hasPackageFrozenTruth,
  isPoolVersionAligned,
  publishPoolStatusMeta,
  publishRuntimeStatusMeta,
  publishSchedulerModeMeta,
} from '../types/creative'
import { useCreativeAuthoringModel } from '../view-models/useCreativeAuthoringModel'
import { useCreativeNavigationState } from '../view-models/useCreativeNavigationState'
import { useCreativePublishDiagnosticsModel } from '../view-models/useCreativePublishDiagnosticsModel'
import { useCreativeVersionReviewModel } from '../view-models/useCreativeVersionReviewModel'

const { Paragraph, Text } = Typography
const { useBreakpoint } = Grid

export default function CreativeDetail() {
  const { message } = App.useApp()
  const screens = useBreakpoint()
  const {
    creativeId,
    prioritizedTaskId,
    detailDiagnosticsOpen,
    aiClipRequested,
    openAiClipWorkflow,
    closeAiClipWorkflow,
    handleOpenDiagnostics,
    handleCloseDiagnostics,
    openTaskDiagnostics,
    openTaskList,
    navigateToDetailReturn,
    onCompositionSubmitted,
  } = useCreativeNavigationState()
  const creativeQuery = useCreative(creativeId)
  const creative = creativeQuery.data

  const {
    currentVersion,
    currentVersionResult,
    versionById,
    currentPackageRecord,
    effectiveCheck,
    effectiveCheckMeta,
    reviewDrawerOpen,
    openReviewDrawer,
    closeReviewDrawer,
    handleOpenAiClipVersion,
    handleReviewVersion,
  } = useCreativeVersionReviewModel({ creative, openAiClipWorkflow })

  const {
    publishStatusQuery,
    scheduleConfigQuery,
    activePoolQuery,
    invalidatedPoolQuery,
    publishStatus,
    creativeFlowMeta,
    creativeFlowShadowCompare,
    activePoolItems,
    invalidatedPoolItems,
    currentPoolItem,
    latestInvalidatedPoolItem,
    currentPoolPackageRecord,
    latestInvalidatedPoolVersion,
    publishPoolRecords,
    diagnosticTaskIds,
    primaryTaskId,
    schedulerMode,
    effectiveSchedulerMode,
    shadowDiff,
    currentPublishTaskId,
    shadowDiffReasons,
    shadowDiffDiffers,
    diagnosticsUnavailable,
    refetchDiagnostics,
    retryDiagnostics,
    schedulerModeLabel,
    effectiveSchedulerModeLabel,
    runtimeStatusLabel,
    shadowReadLabel,
    killSwitchLabel,
  } = useCreativePublishDiagnosticsModel({
    creativeId,
    creative,
    prioritizedTaskId,
    versionById,
    currentPackageRecord,
  })

  const {
    form,
    updateCreative,
    submitCreativeComposition,
    productsQuery,
    watchedCurrentProductName,
    watchedTargetDuration,
    candidateTypeOptions,
    coverNameById,
    profileOptions,
    productOptions,
    materialTypeOptions,
    materialOptionsByType,
    materialLoadingByType,
    canonicalProfileId,
    activeProfile,
    activeInputItemCount,
    handleAdoptCandidateItem,
    handleCandidateItemAssetChange,
    handleCandidateItemTypeChange,
    handleMakePrimaryProductLink,
    handleProductLinkProductChange,
    handleCurrentProductNameChange,
    handleCurrentCopywritingTextChange,
    handleSaveInput,
    handleSubmitComposition,
    submitButtonLabel,
  } = useCreativeAuthoringModel({
    creativeId,
    creative,
    hasCurrentVersion: Boolean(currentVersion),
    messageApi: message,
    refreshCreative: creativeQuery.refetch,
    refreshDiagnostics: refetchDiagnostics,
    onCompositionSubmitted,
  })
  const watchedProductLinks = Form.useWatch('product_links', form) ?? []
  const watchedCandidateItems = Form.useWatch('candidate_items', form) ?? []
  const watchedInputItems = Form.useWatch('input_items', form) ?? []
  const watchedCurrentCopywritingId = Form.useWatch('current_copywriting_id', form)
  const watchedCurrentCopywritingText = Form.useWatch('current_copywriting_text', form)
  const watchedCurrentCoverAssetId = Form.useWatch('current_cover_asset_id', form)
  const watchedCurrentCoverAssetType = Form.useWatch('current_cover_asset_type', form)
  const watchedProductNameMode = Form.useWatch('product_name_mode', form)
  const watchedCoverMode = Form.useWatch('cover_mode', form)
  const watchedCopywritingMode = Form.useWatch('copywriting_mode', form)

  const eligibilityReasons = creative?.eligibility_reasons ?? []
  const statusMeta = creative ? creativeStatusMeta[creative.status] : null
  const aiClipOpen = aiClipRequested && Boolean(currentVersion)
  const detailCardMinWidth = screens.md ? 320 : '100%'
  const aiClipDrawerWidth = screens.xl ? 720 : screens.lg ? 640 : screens.md ? 560 : '100vw'
  const candidateTypes = useMemo(
    () => Object.keys(creativeCandidateMeta) as CreativeAuthoringCandidateType[],
    [],
  )
  const materialNameByType = useMemo(() => ({
    video: new Map((materialOptionsByType.video ?? []).map((item) => [Number(item.value), item.label])),
    audio: new Map((materialOptionsByType.audio ?? []).map((item) => [Number(item.value), item.label])),
    cover: new Map((materialOptionsByType.cover ?? []).map((item) => [Number(item.value), item.label])),
    copywriting: new Map((materialOptionsByType.copywriting ?? []).map((item) => [Number(item.value), item.label])),
  }), [materialOptionsByType])
  const resolveMaterialLabel = useCallback((
    materialType: 'video' | 'audio' | 'copywriting' | 'cover',
    assetId?: number | null,
  ) => {
    if (assetId === undefined || assetId === null) {
      return undefined
    }
    if (materialType === 'cover') {
      return coverNameById.get(assetId) ?? materialNameByType.cover.get(assetId)
    }
    return materialNameByType[materialType].get(assetId)
  }, [coverNameById, materialNameByType])
  const projectionModel = useMemo(() => {
    if (!creative) {
      return null
    }

    return buildCreativeDetailProjectionModel({
      creative,
      draft: {
        currentProductName: watchedCurrentProductName,
        currentCopywritingId: watchedCurrentCopywritingId,
        currentCopywritingText: watchedCurrentCopywritingText,
        currentCoverAssetId: watchedCurrentCoverAssetId,
        currentCoverAssetType: watchedCurrentCoverAssetType,
        productNameMode: watchedProductNameMode,
        coverMode: watchedCoverMode,
        copywritingMode: watchedCopywritingMode,
        productLinks: watchedProductLinks,
        candidateItems: watchedCandidateItems,
        inputItems: watchedInputItems,
      },
      resolveMaterialLabel,
    })
  }, [
    creative,
    resolveMaterialLabel,
    watchedCandidateItems,
    watchedCopywritingMode,
    watchedCoverMode,
    watchedCurrentCopywritingId,
    watchedCurrentCopywritingText,
    watchedCurrentCoverAssetId,
    watchedCurrentCoverAssetType,
    watchedCurrentProductName,
    watchedInputItems,
    watchedProductLinks,
    watchedProductNameMode,
  ])

  const retryCreative = () => {
    void creativeQuery.refetch()
  }

  const eligibilityLabel =
    creative?.eligibility_status === 'READY_TO_COMPOSE'
      ? '待提交合成'
      : creative?.eligibility_status === 'INVALID'
        ? '输入无效'
        : '待补输入'

  const detailActionRecommendations = useMemo<DiagnosticsRecommendation[]>(() => {
    const recommendations: DiagnosticsRecommendation[] = []

    if (diagnosticsUnavailable) {
      recommendations.push({
        key: 'retry-detail-diagnostics',
        title: '高级诊断暂不可用，先重试诊断数据',
        severity: 'warning',
        evidence: [
          `调度模式：${schedulerModeLabel}`,
          `运行状态：${runtimeStatusLabel}`,
        ],
        actionLabel: '重试诊断',
        onAction: retryDiagnostics,
        testId: 'creative-detail-diagnostics-action-retry',
      })
    }

    if (shadowDiffDiffers) {
      recommendations.push({
        key: 'cutover-diff',
        title: 'Cutover 对账存在差异，先阅读下方对账证据',
        severity: 'warning',
        evidence: shadowDiffReasons.length > 0
          ? shadowDiffReasons
          : ['Shadow diff 返回存在差异，但未提供明确原因。'],
      })
    }

    if (primaryTaskId) {
      recommendations.push({
        key: 'primary-task',
        title: '存在主执行任务，优先进入任务诊断',
        severity: 'info',
        evidence: [`主执行任务：#${primaryTaskId}`],
        actionLabel: '查看主执行诊断',
        onAction: () => openTaskDiagnostics(primaryTaskId),
        testId: 'creative-detail-diagnostics-action-primary-task',
      })
    } else if (diagnosticTaskIds.length > 0) {
      recommendations.push({
        key: 'task-list',
        title: '存在执行记录，可进入任务管理继续排查',
        severity: 'info',
        evidence: [`关联执行记录：${diagnosticTaskIds.length} 条`],
        actionLabel: '打开任务管理',
        onAction: openTaskList,
        testId: 'creative-detail-diagnostics-action-task-list',
      })
    } else if (creative?.eligibility_status === 'READY_TO_COMPOSE') {
      recommendations.push({
        key: 'ready-to-compose',
        title: '作品已满足合成条件，请回到主创作区提交',
        severity: 'success',
        evidence: ['诊断抽屉不触发提交合成；提交动作仅保留在主创作区。'],
      })
    } else {
      recommendations.push({
        key: 'complete-authoring',
        title: '当前作品仍需先补齐创作定义',
        severity: creative?.eligibility_status === 'INVALID' ? 'warning' : 'info',
        evidence: eligibilityReasons.length > 0
          ? eligibilityReasons
          : [`合成准备状态：${eligibilityLabel}`],
      })
    }

    if (!currentPoolItem) {
      recommendations.push({
        key: 'missing-pool-item',
        title: '当前版本尚未形成发布侧候选项',
        severity: activePoolQuery.isError ? 'warning' : 'info',
        evidence: [activePoolQuery.isError ? '发布池候选项获取失败。' : '下方发布池证据中暂无当前候选项。'],
      })
    } else if (!isPoolVersionAligned(currentPoolItem)) {
      recommendations.push({
        key: 'unaligned-pool-item',
        title: '发布侧候选项版本未对齐',
        severity: 'warning',
        evidence: [
          `候选项：#${currentPoolItem.id}`,
          `候选版本：#${currentPoolItem.creative_version_id}`,
          `当前版本：#${creative?.current_version_id ?? '-'}`,
        ],
      })
    }

    return recommendations
  }, [
    activePoolQuery.isError,
    creative?.eligibility_status,
    creative?.current_version_id,
    currentPoolItem,
    diagnosticTaskIds.length,
    diagnosticsUnavailable,
    eligibilityLabel,
    eligibilityReasons,
    openTaskDiagnostics,
    openTaskList,
    primaryTaskId,
    retryDiagnostics,
    runtimeStatusLabel,
    schedulerModeLabel,
    shadowDiffDiffers,
    shadowDiffReasons,
  ])
  const scrollToSection = useCallback((sectionId: string) => {
    if (typeof document === 'undefined') {
      return
    }
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  if (creativeQuery.isLoading && !creative) {
    return (
      <Flex justify="center" style={{ padding: 48 }} data-testid="creative-detail-loading">
        <Spin size="large" />
      </Flex>
    )
  }

  if (creativeQuery.isError) {
    return (
      <PageContainer title="作品详情" onBack={navigateToDetailReturn}>
        <div data-testid="creative-detail-error">
          <Result
            status="error"
            title="作品详情暂时无法加载"
            subTitle="详情加载失败，当前无法继续查看输入、版本或审核信息。"
            extra={[
              <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={retryCreative}>
                重试加载
              </Button>,
              <Button key="back" onClick={navigateToDetailReturn}>
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
      <PageContainer title="作品详情" onBack={navigateToDetailReturn}>
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
      onBack={navigateToDetailReturn}
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
          <Button key="review" type="primary" data-testid="creative-open-review" onClick={openReviewDrawer}>
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

        {projectionModel ? (
          <>
            <CreativeDetailHeroCard
              creative={creative}
              projection={projectionModel}
              statusMeta={statusMeta}
              activeInputItemCount={activeInputItemCount}
              submitButtonLabel={submitButtonLabel}
              submitDisabled={creative.eligibility_status !== 'READY_TO_COMPOSE' || updateCreative.isPending}
              submitLoading={submitCreativeComposition.isPending}
              saveLoading={updateCreative.isPending}
              onSubmit={() => void handleSubmitComposition()}
              onSave={() => void handleSaveInput()}
              onOpenDiagnostics={handleOpenDiagnostics}
              onJumpToEditor={() => scrollToSection('creative-detail-legacy-editor')}
            />

            <CreativeCurrentSelectionSection projection={projectionModel} />

            <Flex gap={16} wrap="wrap" align="stretch">
              <CreativeSourceZoneSection
                title="B. 商品区"
                subtitle="主题商品与默认来源"
                description="商品区负责承接主题商品、默认商品名称，以及来自商品侧的封面 / 视频 / 文案候选。"
                action={(
                  <Button size="small" onClick={() => scrollToSection('creative-detail-product-editor')}>
                    编辑商品区
                  </Button>
                )}
                summary={projectionModel.productZone.primary_product ? (
                  <Card size="small" type="inner" title="当前主题商品摘要">
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      <Text strong>{projectionModel.productZone.primary_product.name}</Text>
                      <Space wrap>
                        <Tag color="processing">主题商品</Tag>
                        <Tag>商品 ID：{projectionModel.productZone.primary_product.id}</Tag>
                        <Tag>封面 {projectionModel.productZone.primary_product.cover_count ?? 0}</Tag>
                        <Tag>视频 {projectionModel.productZone.primary_product.video_count ?? 0}</Tag>
                        <Tag>文案 {projectionModel.productZone.primary_product.copywriting_count ?? 0}</Tag>
                      </Space>
                      {projectionModel.productZone.product_name_candidate ? (
                        <Text type="secondary">
                          默认商品名称：{projectionModel.productZone.product_name_candidate.product_name}
                          {projectionModel.productZone.product_name_candidate.is_detached ? '（当前已脱钩）' : ''}
                        </Text>
                      ) : null}
                      {(projectionModel.productZone.linked_products ?? []).length > 0 ? (
                        <Space wrap>
                          {(projectionModel.productZone.linked_products ?? []).map((product) => (
                            <Tag key={`${product.product_id}-${product.sort_order}`} color={product.is_primary ? 'processing' : 'default'}>
                              {product.product_name ?? `商品 #${product.product_id}`}
                            </Tag>
                          ))}
                        </Space>
                      ) : null}
                    </Space>
                  </Card>
                ) : (
                  <Alert
                    type="info"
                    showIcon
                    message="当前还没有主题商品"
                    description="先在商品区建立主题商品，页面才能形成更稳定的默认候选。"
                  />
                )}
                candidates={[
                  {
                    key: 'product-cover',
                    label: '封面候选',
                    items: projectionModel.productZone.cover_candidates ?? [],
                    emptyDescription: '当前商品区还没有可用封面候选。',
                  },
                  {
                    key: 'product-video',
                    label: '视频候选',
                    items: projectionModel.productZone.video_candidates ?? [],
                    emptyDescription: '当前商品区还没有可用视频候选。',
                  },
                  {
                    key: 'product-copywriting',
                    label: '文案候选',
                    items: projectionModel.productZone.copywriting_candidates ?? [],
                    emptyDescription: '当前商品区还没有可用文案候选。',
                  },
                ]}
                testId="creative-detail-product-zone"
              />

              <CreativeSourceZoneSection
                title="C. 自由素材区"
                subtitle="补充来源区"
                description="自由素材区负责承接非主题商品来源的补充素材，不抢占首屏主角，但要能清楚表达哪些素材已被当前作品采用。"
                action={(
                  <Button size="small" onClick={() => scrollToSection('creative-detail-candidate-editor')}>
                    管理自由素材
                  </Button>
                )}
                summary={(
                  <Alert
                    type="info"
                    showIcon
                    message="自由素材区用于补充封面 / 视频 / 音频 / 文案来源"
                    description="这里的素材可以被勾选到当前作品，但最终生效值仍以“当前入选区”为准。"
                  />
                )}
                candidates={[
                  {
                    key: 'free-cover',
                    label: '封面候选',
                    items: projectionModel.freeMaterialZone.cover_candidates ?? [],
                    emptyDescription: '当前还没有自由封面候选。',
                  },
                  {
                    key: 'free-video',
                    label: '视频候选',
                    items: projectionModel.freeMaterialZone.video_candidates ?? [],
                    emptyDescription: '当前还没有自由视频候选。',
                  },
                  {
                    key: 'free-audio',
                    label: '音频候选',
                    items: projectionModel.freeMaterialZone.audio_candidates ?? [],
                    emptyDescription: '当前还没有自由音频候选。',
                  },
                  {
                    key: 'free-copywriting',
                    label: '文案候选',
                    items: projectionModel.freeMaterialZone.copywriting_candidates ?? [],
                    emptyDescription: '当前还没有自由文案候选。',
                  },
                ]}
                testId="creative-detail-free-material-zone"
              />
            </Flex>
          </>
        ) : null}

        <Card
          id="creative-detail-legacy-editor"
          data-testid="creative-detail-legacy-editor"
          title="定义编辑区（兼容编辑）"
          extra={(
            <Space wrap>
              <Text type="secondary">入选媒体：{activeInputItemCount}</Text>
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
              P0-2 之后，首屏改由“当前入选区 + 来源区”承接；这里保留兼容编辑能力，用于继续维护作品级商品、候选池与入选媒体。
            </Paragraph>

            <ProDescriptions bordered size="small" column={screens.lg ? 4 : screens.md ? 2 : 1}>
              <ProDescriptions.Item label="主体商品">
                {watchedCurrentProductName || creative.current_product_name || creative.subject_product_name_snapshot || '待补充'}
              </ProDescriptions.Item>
              <ProDescriptions.Item label="目标时长">
                {formatCreativeDuration(watchedTargetDuration ?? creative.target_duration_seconds)}
              </ProDescriptions.Item>
              <ProDescriptions.Item label="启用入选媒体">{activeInputItemCount}</ProDescriptions.Item>
              <ProDescriptions.Item label="合成配置">
                {activeProfile?.name ?? (canonicalProfileId ? `配置 #${canonicalProfileId}` : '待选择')}
              </ProDescriptions.Item>
            </ProDescriptions>

            <Form form={form} layout="vertical">
              <Form.Item name="product_name_mode" hidden><Input /></Form.Item>
              <Form.Item name="current_cover_asset_type" hidden><Input /></Form.Item>
              <Form.Item name="current_cover_asset_id" hidden><InputNumber /></Form.Item>
              <Form.Item name="cover_mode" hidden><Input /></Form.Item>
              <Form.Item name="current_copywriting_id" hidden><InputNumber /></Form.Item>
              <Form.Item name="copywriting_mode" hidden><Input /></Form.Item>
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

              <div id="creative-detail-product-editor">
                <Form.List name="product_links">
                  {(fields, { add, move, remove }) => (
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Flex justify="space-between" align="center" wrap="wrap" gap={12}>
                      <Space direction="vertical" size={0}>
                        <Text strong>关联商品（product_links）</Text>
                        <Text type="secondary">一个作品可关联多个商品；主题商品唯一，并驱动默认商品名 / 封面来源。</Text>
                      </Space>
                      <Button
                        type="dashed"
                        icon={<PlusOutlined />}
                        onClick={() => add({ enabled: true, is_primary: fields.length === 0, source_mode: 'manual_add' })}
                        data-testid="creative-detail-add-product-link"
                      >
                        添加关联商品
                      </Button>
                    </Flex>

                    {fields.length === 0 ? (
                      <Alert
                        type="info"
                        showIcon
                        message="当前还没有关联商品"
                        description="请至少添加 1 个商品；第一个有效商品会自动成为主题商品。"
                      />
                    ) : null}

                    {fields.map((field, index) => {
                      const isPrimary = Boolean(form.getFieldValue(['product_links', field.name, 'is_primary']))
                      const selectedProductId = form.getFieldValue(['product_links', field.name, 'product_id']) as number | undefined
                      return (
                        <Card
                          key={field.key}
                          type="inner"
                          size="small"
                          title={`关联商品 ${index + 1}`}
                          extra={(
                            <Space wrap>
                              <Tag color={isPrimary ? 'processing' : 'default'}>
                                {isPrimary ? '主题商品' : '关联商品'}
                              </Tag>
                              <Button
                                size="small"
                                disabled={index === 0}
                                icon={<ArrowUpOutlined />}
                                onClick={() => move(index, index - 1)}
                                data-testid={`creative-detail-product-link-up-${index}`}
                              >
                                上移
                              </Button>
                              <Button
                                size="small"
                                disabled={index === fields.length - 1}
                                icon={<ArrowDownOutlined />}
                                onClick={() => move(index, index + 1)}
                                data-testid={`creative-detail-product-link-down-${index}`}
                              >
                                下移
                              </Button>
                              <Button
                                size="small"
                                type={isPrimary ? 'primary' : 'default'}
                                disabled={isPrimary || !selectedProductId}
                                onClick={() => handleMakePrimaryProductLink(index)}
                                data-testid={`creative-detail-product-link-primary-${index}`}
                              >
                                {isPrimary ? '当前主题商品' : '设为主题商品'}
                              </Button>
                              <Button
                                size="small"
                                danger
                                disabled={isPrimary}
                                icon={<DeleteOutlined />}
                                onClick={() => remove(index)}
                                data-testid={`creative-detail-product-link-remove-${index}`}
                              >
                                移除
                              </Button>
                            </Space>
                          )}
                        >
                          <Form.Item name={[field.name, 'is_primary']} hidden valuePropName="checked"><Switch /></Form.Item>
                          <Form.Item name={[field.name, 'source_mode']} hidden><Input /></Form.Item>
                          <Flex gap={16} wrap="wrap" align="start">
                            <Form.Item
                              {...field}
                              name={[field.name, 'product_id']}
                              label="关联商品"
                              rules={[{ required: true, message: '请选择关联商品' }]}
                              style={{ flex: 1, minWidth: 260 }}
                            >
                              <Select
                                allowClear
                                showSearch
                                optionFilterProp="label"
                                placeholder="选择关联商品"
                                options={productOptions}
                                loading={productsQuery.isLoading}
                                onChange={(value) => handleProductLinkProductChange(index, value)}
                                data-testid={`creative-detail-product-link-select-${index}`}
                              />
                            </Form.Item>
                            <Form.Item
                              name={[field.name, 'enabled']}
                              label="启用"
                              valuePropName="checked"
                              style={{ width: screens.md ? 120 : '100%' }}
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
              </div>

              <Flex gap={16} wrap="wrap" align="start" style={{ marginTop: 16 }}>
                <Form.Item
                  name="current_product_name"
                  label="商品名称快照"
                  style={{ flex: 1, minWidth: 260 }}
                >
                  <Input
                    placeholder="用于作品 brief / 版本沉淀的商品名称"
                    allowClear
                    onChange={(event) => handleCurrentProductNameChange(event.target.value)}
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

              <Form.Item name="current_copywriting_text" label="主文案">
                <Input.TextArea
                  autoSize={{ minRows: 3, maxRows: 6 }}
                  placeholder="填写作品级主文案；它属于作品 brief，而不是单个素材条目。"
                  onChange={(event) => handleCurrentCopywritingTextChange(event.target.value)}
                  data-testid="creative-detail-main-copywriting"
                />
              </Form.Item>

              <div id="creative-detail-candidate-editor">
                <Form.List name="candidate_items">
                  {(fields, { add, remove }) => (
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Alert
                      type="info"
                      showIcon
                      message="作品候选池（candidate_items）"
                      description={`这里维护作品级候选池；当前商品名：${watchedCurrentProductName || '未设定'}。当前封面：${(() => {
                        const coverId = form.getFieldValue('current_cover_asset_id') as number | undefined
                        return coverId ? (coverNameById.get(coverId) ?? `封面 #${coverId}`) : '未采用候选'
                      })()}。视频 / 音频候选在本 Slice 只进入候选池，不会自动进入当前入选媒体集合。`}
                    />

                    {candidateTypes.map((sectionType) => {
                      const sectionFields = fields.filter((field) => {
                        const candidateType =
                          (form.getFieldValue(['candidate_items', field.name, 'candidate_type']) as CreativeAuthoringCandidateType | undefined)
                          ?? sectionType
                        return candidateType === sectionType
                      })
                      const sectionLabel = creativeCandidateMeta[sectionType].label
                      const sectionOptions = materialOptionsByType[sectionType] ?? []
                      const sectionLoading = materialLoadingByType[sectionType] ?? false

                      return (
                        <Card
                          key={sectionType}
                          type="inner"
                          size="small"
                          title={sectionLabel}
                          extra={(
                            <Button
                              type="dashed"
                              size="small"
                              icon={<PlusOutlined />}
                              onClick={() => add({
                                candidate_type: sectionType,
                                source_kind: 'material_library',
                                enabled: true,
                                status: 'candidate',
                              })}
                              data-testid={`creative-detail-add-candidate-${sectionType}`}
                            >
                              添加{sectionLabel}
                            </Button>
                          )}
                        >
                          {sectionFields.length === 0 ? (
                            <Empty
                              image={Empty.PRESENTED_IMAGE_SIMPLE}
                              description={`当前还没有${sectionLabel}`}
                            />
                          ) : (
                            <Space direction="vertical" size={12} style={{ width: '100%' }}>
                              {sectionFields.map((field, index) => {
                                const candidateType =
                                  (form.getFieldValue(['candidate_items', field.name, 'candidate_type']) as CreativeAuthoringCandidateType | undefined)
                                  ?? sectionType
                                const status =
                                  (form.getFieldValue(['candidate_items', field.name, 'status']) as string | undefined)
                                  ?? 'candidate'
                                const assetId = form.getFieldValue(['candidate_items', field.name, 'asset_id']) as number | undefined
                                const candidateMeta = creativeCandidateMeta[candidateType]
                                const candidateOptions = materialOptionsByType[candidateType] ?? sectionOptions
                                const candidateLoading = materialLoadingByType[candidateType] ?? sectionLoading

                                return (
                                  <Card
                                    key={field.key}
                                    type="inner"
                                    size="small"
                                    title={`${candidateMeta.label} ${index + 1}`}
                                    extra={(
                                      <Space wrap>
                                        <Tag color={status === 'adopted' ? 'processing' : status === 'dismissed' ? 'default' : 'success'}>
                                          {status === 'adopted' ? '已采用' : status === 'dismissed' ? '已忽略' : '候选中'}
                                        </Tag>
                                        {candidateType === 'cover' || candidateType === 'copywriting' ? (
                                          <Button
                                            size="small"
                                            type={status === 'adopted' ? 'primary' : 'default'}
                                            disabled={!assetId}
                                            onClick={() => handleAdoptCandidateItem(field.name)}
                                            data-testid={`creative-detail-adopt-candidate-${candidateType}-${index}`}
                                          >
                                            {status === 'adopted' ? '当前已采用' : candidateMeta.adoptLabel}
                                          </Button>
                                        ) : null}
                                        <Button
                                          size="small"
                                          danger
                                          icon={<DeleteOutlined />}
                                          onClick={() => remove(field.name)}
                                          data-testid={`creative-detail-remove-candidate-${candidateType}-${index}`}
                                        >
                                          移除
                                        </Button>
                                      </Space>
                                    )}
                                  >
                                    <Flex gap={16} wrap="wrap" align="start">
                                      <Form.Item
                                        name={[field.name, 'candidate_type']}
                                        label="候选类型"
                                        rules={[{ required: true, message: '请选择候选类型' }]}
                                        style={{ minWidth: 180, flex: 1 }}
                                      >
                                        <Select
                                          options={candidateTypeOptions}
                                          onChange={(value) => handleCandidateItemTypeChange(field.name, value)}
                                          data-testid={`creative-detail-candidate-type-${candidateType}-${index}`}
                                        />
                                      </Form.Item>

                                      <Form.Item
                                        name={[field.name, 'asset_id']}
                                        label="候选素材"
                                        rules={[{ required: true, message: '请选择候选素材' }]}
                                        style={{ minWidth: 240, flex: 1.4 }}
                                      >
                                        <Select
                                          allowClear
                                          showSearch
                                          optionFilterProp="label"
                                          placeholder={`选择${candidateMeta.label}`}
                                          options={candidateOptions}
                                          loading={candidateLoading}
                                          onChange={(value) => handleCandidateItemAssetChange(field.name, value)}
                                          data-testid={`creative-detail-candidate-asset-${candidateType}-${index}`}
                                        />
                                      </Form.Item>

                                      <Form.Item
                                        name={[field.name, 'source_kind']}
                                        label="来源"
                                        style={{ minWidth: 180, flex: 1 }}
                                      >
                                        <Select
                                          options={[
                                            { value: 'material_library', label: '素材库' },
                                            { value: 'product_derived', label: '商品派生' },
                                            { value: 'manual_upload', label: '手工上传' },
                                            { value: 'llm_generated', label: '模型生成' },
                                          ]}
                                          data-testid={`creative-detail-candidate-source-${candidateType}-${index}`}
                                        />
                                      </Form.Item>

                                      <Form.Item
                                        name={[field.name, 'status']}
                                        label="状态"
                                        style={{ width: screens.md ? 160 : '100%' }}
                                      >
                                        <Select
                                          options={[
                                            { value: 'candidate', label: '候选中' },
                                            { value: 'dismissed', label: '已忽略' },
                                          ]}
                                          data-testid={`creative-detail-candidate-status-${candidateType}-${index}`}
                                        />
                                      </Form.Item>

                                      <Form.Item
                                        name={[field.name, 'enabled']}
                                        label="启用"
                                        valuePropName="checked"
                                        style={{ width: screens.md ? 120 : '100%' }}
                                      >
                                        <Switch checkedChildren="启用" unCheckedChildren="停用" />
                                      </Form.Item>
                                    </Flex>
                                  </Card>
                                )
                              })}
                            </Space>
                          )}
                        </Card>
                      )
                    })}
                    </Space>
                  )}
                </Form.List>
              </div>

              <div id="creative-detail-selected-media-editor">
                <Form.List name="input_items">
                  {(fields, { add, move, remove }) => (
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Flex justify="space-between" align="center" wrap="wrap" gap={12}>
                      <Space direction="vertical" size={0}>
                        <Text strong>当前入选媒体集合（selected video / audio）</Text>
                        <Text type="secondary">基于 detail.input_items 的 full-carrier 读回，仅展示并维护其中的视频 / 音频条目；封面 / 文案 / 话题不再从这里写回。</Text>
                      </Space>
                      <Button
                        type="dashed"
                        icon={<PlusOutlined />}
                        onClick={() => add({ material_type: 'video', enabled: true })}
                        data-testid="creative-detail-add-input-item"
                      >
                        添加入选媒体
                      </Button>
                    </Flex>

                    {fields.length === 0 ? (
                      <Alert
                        type="info"
                        showIcon
                        message="当前还没有入选媒体"
                        description="请至少添加 1 条视频或音频；如需重复使用同一素材，可重复加入当前入选媒体集合。"
                      />
                    ) : null}

                    {fields.map((field, index) => {
                      const materialType =
                        (form.getFieldValue(['input_items', field.name, 'material_type']) as CreativeSelectedMediaType | undefined)
                        ?? 'video'
                      const materialOptions = materialOptionsByType[materialType] ?? []

                      return (
                        <Card
                          key={field.key}
                          type="inner"
                          size="small"
                          title={`入选媒体 ${index + 1}`}
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
                              label="媒体类型"
                              rules={[{ required: true, message: '请选择媒体类型' }]}
                              style={{ minWidth: 160, flex: 1 }}
                            >
                              <Select
                                options={materialTypeOptions}
                                data-testid={`creative-detail-input-item-type-${index}`}
                              />
                            </Form.Item>

                            <Form.Item
                              name={[field.name, 'material_id']}
                              label={creativeSelectedMediaMeta[materialType].label}
                              rules={[{ required: true, message: '请选择媒体素材' }]}
                              style={{ minWidth: 220, flex: 1.4 }}
                            >
                              <Select
                                allowClear
                                showSearch
                                optionFilterProp="label"
                                placeholder={`选择${creativeSelectedMediaMeta[materialType].label}`}
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
              </div>
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
            {currentVersionResult ? (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <ProDescriptions bordered size="small" column={screens.md ? 2 : 1}>
                  <ProDescriptions.Item label="版本 ID">{currentVersionResult.id}</ProDescriptions.Item>
                  <ProDescriptions.Item label="版本号">{getVersionLabel(currentVersionResult.version_no)}</ProDescriptions.Item>
                  <ProDescriptions.Item label="版本标题" span={2}>{currentVersionResult.title ?? '未命名版本'}</ProDescriptions.Item>
                  <ProDescriptions.Item label="父版本 ID">{currentVersionResult.parent_version_id ?? '-'}</ProDescriptions.Item>
                  <ProDescriptions.Item label="发布侧 PackageRecord">{currentVersionResult.package_record_id ?? '-'}</ProDescriptions.Item>
                  <ProDescriptions.Item label="结果时长">
                    {formatCreativeDurationSeconds(currentVersionResult.actual_duration_seconds)}
                  </ProDescriptions.Item>
                  <ProDescriptions.Item label="成片路径">
                    {formatCreativeText(currentVersionResult.final_video_path)}
                  </ProDescriptions.Item>
                  <ProDescriptions.Item label="最终商品名">
                    {formatCreativeText(currentVersionResult.final_product_name)}
                  </ProDescriptions.Item>
                  <ProDescriptions.Item label="最终文案" span={2}>
                    {formatCreativeText(currentVersionResult.final_copywriting_text)}
                  </ProDescriptions.Item>
                </ProDescriptions>
                <Paragraph type="secondary" style={{ marginBottom: 0 }} data-testid="creative-current-version-semantics">
                  版本结果承接当前作品 brief 与素材编排，并沉淀 adopted truth；发布包冻结值承接发布四件套，执行任务只在高级诊断中作为运行载体出现。
                </Paragraph>
                <Card
                  size="small"
                  type="inner"
                  title="当前发布包冻结值"
                  data-testid="creative-current-package-freeze"
                >
                  {currentPackageRecord ? (
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      <Text type="secondary">
                        PackageRecord #{currentPackageRecord.id}
                        {currentPackageRecord.publish_profile_id ? ` / 发布档案 #${currentPackageRecord.publish_profile_id}` : ''}
                      </Text>
                      {hasPackageFrozenTruth(currentPackageRecord) ? (
                        <ProDescriptions size="small" column={1}>
                          <ProDescriptions.Item label="冻结视频">
                            {formatCreativeText(currentPackageRecord.frozen_video_path)}
                          </ProDescriptions.Item>
                          <ProDescriptions.Item label="冻结封面">
                            {formatCreativeText(currentPackageRecord.frozen_cover_path)}
                          </ProDescriptions.Item>
                          <ProDescriptions.Item label="冻结时长">
                            {formatCreativeDurationSeconds(currentPackageRecord.frozen_duration_seconds)}
                          </ProDescriptions.Item>
                          <ProDescriptions.Item label="冻结商品名">
                            {formatCreativeText(currentPackageRecord.frozen_product_name)}
                          </ProDescriptions.Item>
                          <ProDescriptions.Item label="冻结文案">
                            {formatCreativeText(currentPackageRecord.frozen_copywriting_text)}
                          </ProDescriptions.Item>
                        </ProDescriptions>
                      ) : (
                        <Alert
                          type="info"
                          showIcon
                          message="当前版本已关联发布包，但冻结四件套尚未返回。"
                        />
                      )}
                    </Space>
                  ) : (
                    <Alert
                      type="info"
                      showIcon
                      message="当前版本尚未生成发布包冻结值。"
                    />
                  )}
                </Card>
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
          onOpenAiClipWorkflow={handleOpenAiClipVersion}
          onReviewVersion={handleReviewVersion}
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
          <DiagnosticsActionPanel
            title="当前作品建议"
            recommendations={detailActionRecommendations}
            testId="creative-detail-diagnostics-actions"
          />

          <Card title="执行任务诊断" size="small" data-testid="creative-task-diagnostics-card">
            {diagnosticTaskIds.length > 0 ? (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0 }} data-testid="creative-task-diagnostics-note">
                  任务管理只承接执行进度、失败重试与排障，不回写作品定义、版本结果或发布包冻结值。
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
                  <Button onClick={openTaskList}>打开任务管理</Button>
                </Space>
              </Space>
            ) : (
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  这条作品还没有关联执行记录；如需排查执行侧信息，可从这里进入任务管理。
                </Paragraph>
                <Button onClick={openTaskList}>打开任务管理</Button>
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
              这里查看发布包冻结值、发布侧候选项、调度模式与 cutover 对账；如果当前作品定义暂不能直达发布，表示当前执行引擎能力尚未覆盖，并不代表作品定义无效。
            </Paragraph>
            <ProDescriptions bordered size="small" column={screens.md ? 2 : 1}>
              <ProDescriptions.Item label="入口模式">
                <Space wrap>
                  <Tag>{creativeFlowMeta.label}</Tag>
                  <Tag>{creativeFlowShadowCompare ? 'Shadow Compare：开启' : 'Shadow Compare：关闭'}</Tag>
                </Space>
              </ProDescriptions.Item>
              <ProDescriptions.Item label="调度模式">
                <Tag color={publishStatusQuery.isError && scheduleConfigQuery.isError ? 'warning' : schedulerMode ? publishSchedulerModeMeta[schedulerMode].color : 'default'}>
                  {schedulerModeLabel}
                </Tag>
              </ProDescriptions.Item>
              <ProDescriptions.Item label="当前生效模式">
                <Tag color={publishStatusQuery.isError ? 'warning' : effectiveSchedulerMode ? publishSchedulerModeMeta[effectiveSchedulerMode].color : 'default'}>
                  {effectiveSchedulerModeLabel}
                </Tag>
              </ProDescriptions.Item>
              <ProDescriptions.Item label="运行状态">
                <Tag color={publishStatusQuery.isError ? 'warning' : publishStatus?.status ? publishRuntimeStatusMeta[publishStatus.status].color : 'default'}>
                  {runtimeStatusLabel}
                </Tag>
              </ProDescriptions.Item>
              <ProDescriptions.Item label="当前发布执行任务">
                {currentPublishTaskId !== null ? (
                  <Button type="link" onClick={() => openTaskDiagnostics(currentPublishTaskId)}>
                    任务 #{currentPublishTaskId}
                  </Button>
                ) : publishStatusQuery.isError ? '获取失败' : '-'}
              </ProDescriptions.Item>
              <ProDescriptions.Item label="Shadow Read">{shadowReadLabel}</ProDescriptions.Item>
              <ProDescriptions.Item label="Kill Switch">{killSwitchLabel}</ProDescriptions.Item>
              <ProDescriptions.Item label="当前发布侧候选项">
                {currentPoolItem ? (
                  <Space wrap>
                    <Tag color={publishPoolStatusMeta[currentPoolItem.status].color}>{publishPoolStatusMeta[currentPoolItem.status].label}</Tag>
                    <Tag color={isPoolVersionAligned(currentPoolItem) ? 'success' : 'warning'}>版本 #{currentPoolItem.creative_version_id}</Tag>
                    {currentPoolPackageRecord ? <Tag>Package #{currentPoolPackageRecord.id}</Tag> : null}
                  </Space>
                ) : activePoolQuery.isError ? '获取失败' : '当前版本尚未生成发布侧候选项'}
              </ProDescriptions.Item>
              <ProDescriptions.Item label="候选项 ID">
                {currentPoolItem ? `#${currentPoolItem.id}` : activePoolQuery.isError ? '获取失败' : '-'}
              </ProDescriptions.Item>
              <ProDescriptions.Item label="当前发布包冻结值" span={2}>
                {currentPoolPackageRecord ? (
                  <Space direction="vertical" size={4} data-testid="creative-current-publish-package-summary">
                    <Text>Package #{currentPoolPackageRecord.id}</Text>
                    <Text type="secondary">冻结商品名：{formatCreativeText(currentPoolPackageRecord.frozen_product_name)}</Text>
                    <Text type="secondary">冻结文案：{formatCreativeText(currentPoolPackageRecord.frozen_copywriting_text)}</Text>
                    <Text type="secondary">冻结视频：{formatCreativeText(currentPoolPackageRecord.frozen_video_path)}</Text>
                    <Text type="secondary">冻结时长：{formatCreativeDurationSeconds(currentPoolPackageRecord.frozen_duration_seconds)}</Text>
                    <Text type="secondary">冻结封面：{formatCreativeText(currentPoolPackageRecord.frozen_cover_path)}</Text>
                  </Space>
                ) : activePoolQuery.isError ? '获取失败' : '当前候选项尚未返回发布包冻结值'}
              </ProDescriptions.Item>
              <ProDescriptions.Item label="当前 package / task 关系" span={2}>
                {currentPoolPackageRecord ? (
                  <Space wrap>
                    <Tag>Package #{currentPoolPackageRecord.id}</Tag>
                    <Tag>版本 #{currentPoolItem?.creative_version_id ?? currentVersionResult?.id ?? '-'}</Tag>
                    <Tag>{currentPublishTaskId !== null ? `任务 #${currentPublishTaskId}` : '暂无发布执行任务'}</Tag>
                  </Space>
                ) : activePoolQuery.isError ? '获取失败' : '当前暂无 package / task 关系可展示'}
              </ProDescriptions.Item>
              <ProDescriptions.Item label="最近候选失效记录" span={2}>
                {latestInvalidatedPoolItem ? (
                  <Space direction="vertical" size={4}>
                    <Text>Pool #{latestInvalidatedPoolItem.id} / 版本 #{latestInvalidatedPoolItem.creative_version_id}</Text>
                    {latestInvalidatedPoolVersion?.package_record ? (
                      <Text type="secondary">关联 Package #{latestInvalidatedPoolVersion.package_record.id}</Text>
                    ) : null}
                    <Text type="secondary">失效于 {formatCreativeTimestamp(latestInvalidatedPoolItem.invalidated_at ?? latestInvalidatedPoolItem.updated_at)}</Text>
                    <Text type="secondary">原因：{latestInvalidatedPoolItem.invalidation_reason ?? '未记录'}</Text>
                  </Space>
                ) : invalidatedPoolQuery.isError ? '获取失败' : '暂无失效记录'}
              </ProDescriptions.Item>
            </ProDescriptions>
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
                dataSource={publishPoolRecords}
                renderItem={({ item, aligned, packageRecord }) => {
                  return (
                    <List.Item key={`${item.status}-${item.id}`} data-testid={`creative-pool-item-${item.id}`}>
                      <Space direction="vertical" size={6} style={{ width: '100%' }}>
                        <Space wrap>
                          <Tag color={publishPoolStatusMeta[item.status].color}>{publishPoolStatusMeta[item.status].label}</Tag>
                          <Tag color={aligned ? 'success' : 'warning'}>版本 #{item.creative_version_id}</Tag>
                          <Tag color={aligned ? 'success' : 'warning'}>{aligned ? '发布侧已对齐' : '发布侧存在偏差'}</Tag>
                          <Tag>Pool #{item.id}</Tag>
                          {packageRecord ? <Tag>Package #{packageRecord.id}</Tag> : null}
                        </Space>
                        <Text type="secondary">入池于 {formatCreativeTimestamp(item.created_at)}，最近更新时间 {formatCreativeTimestamp(item.updated_at)}</Text>
                        {packageRecord ? (
                          <Space
                            direction="vertical"
                            size={2}
                            style={{ width: '100%' }}
                            data-testid={`creative-pool-item-freeze-${item.id}`}
                          >
                            <Text type="secondary">冻结商品名：{formatCreativeText(packageRecord.frozen_product_name)}</Text>
                            <Text type="secondary">冻结文案：{formatCreativeText(packageRecord.frozen_copywriting_text)}</Text>
                            <Text type="secondary">冻结视频：{formatCreativeText(packageRecord.frozen_video_path)}</Text>
                            <Text type="secondary">冻结时长：{formatCreativeDurationSeconds(packageRecord.frozen_duration_seconds)}</Text>
                          </Space>
                        ) : (
                          <Text type="secondary" data-testid={`creative-pool-item-freeze-${item.id}`}>
                            当前候选项尚未返回发布包冻结值
                          </Text>
                        )}
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

      <CheckDrawer creativeId={creativeId} open={reviewDrawerOpen} version={currentVersion} onClose={closeReviewDrawer} />

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
