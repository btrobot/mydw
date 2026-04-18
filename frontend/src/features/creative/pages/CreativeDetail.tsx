import { PageContainer } from '@ant-design/pro-components'
import { useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Collapse,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  List,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd'

import AIClipWorkflowPanel from '../components/AIClipWorkflowPanel'
import CheckDrawer from '../components/CheckDrawer'
import VersionPanel from '../components/VersionPanel'
import {
  useCreative,
  usePublishPoolItems,
  usePublishStatus,
  useScheduleConfig,
} from '../hooks/useCreatives'
import {
  creativeReviewConclusionMeta,
  creativeStatusMeta,
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

export default function CreativeDetail() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const creativeId = id ? Number.parseInt(id, 10) : undefined
  const { data: creative, isLoading, isError } = useCreative(creativeId)
  const { data: publishStatus, isError: publishStatusError } = usePublishStatus()
  const { data: scheduleConfig, isError: scheduleConfigError } = useScheduleConfig()
  const { data: activePoolData, isError: activePoolError } = usePublishPoolItems({
    creativeId,
    status: 'active',
    limit: 50,
    enabled: creativeId !== undefined,
  })
  const { data: invalidatedPoolData, isError: invalidatedPoolError } = usePublishPoolItems({
    creativeId,
    status: 'invalidated',
    limit: 50,
    enabled: creativeId !== undefined,
  })
  const [drawerOpen, setDrawerOpen] = useState(false)

  const currentVersion = creative?.versions?.find((version) => version.is_current) ?? null
  const aiClipOpen = searchParams.get('tool') === 'ai-clip' && Boolean(currentVersion)

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

  const activePoolItems = activePoolData?.items ?? []
  const invalidatedPoolItems = useMemo(
    () => [...(invalidatedPoolData?.items ?? [])].sort((left, right) => right.updated_at.localeCompare(left.updated_at)),
    [invalidatedPoolData?.items],
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
  const primaryTaskId = useMemo(() => creative?.linked_task_ids?.[0], [creative?.linked_task_ids])

  const diagnosticTaskIds = useMemo(() => {
    const ids = new Set<number>()
    for (const taskId of creative?.linked_task_ids ?? []) {
      ids.add(taskId)
    }
    if (publishStatus?.current_task_id) {
      ids.add(publishStatus.current_task_id)
    }
    return Array.from(ids)
  }, [creative?.linked_task_ids, publishStatus?.current_task_id])

  const statusMeta = creative ? creativeStatusMeta[creative.status] : null
  const effectiveCheck = creative?.review_summary?.current_check
  const effectiveCheckMeta = effectiveCheck ? creativeReviewConclusionMeta[effectiveCheck.conclusion] : null

  const schedulerMode = publishStatus?.scheduler_mode ?? scheduleConfig?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatus?.effective_scheduler_mode ?? schedulerMode
  const shadowDiff = publishStatus?.scheduler_shadow_diff
  const shadowDiffReasons = formatShadowDiffReasons(shadowDiff)
  const shadowDiffDiffers = getShadowDiffFlag(shadowDiff)
  const diagnosticsUnavailable = publishStatusError || scheduleConfigError || activePoolError || invalidatedPoolError

  if (isLoading) {
    return <Flex justify="center" style={{ padding: 48 }}><Spin size="large" /></Flex>
  }

  if (!creative || isError || !statusMeta) {
    return (
      <PageContainer title="作品详情" onBack={() => navigate('/creative/workbench')}>
        <Empty description="作品不存在，或你没有权限查看该记录" />
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
              message="诊断信息暂不可用"
              description="发布状态、调度配置或发布池数据加载失败，请稍后重试或转到任务诊断页继续排查。"
              style={{ marginBottom: 16 }}
            />
          ) : null}
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="调度模式">
              <Tag color={schedulerMode ? publishSchedulerModeMeta[schedulerMode].color : 'default'}>{formatModeLabel(schedulerMode)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前生效模式">
              <Tag color={effectiveSchedulerMode ? publishSchedulerModeMeta[effectiveSchedulerMode].color : 'default'}>{formatModeLabel(effectiveSchedulerMode)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="运行状态">
              <Tag color={publishStatus?.status ? publishRuntimeStatusMeta[publishStatus.status].color : 'default'}>{formatRuntimeStatusLabel(publishStatus?.status)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前任务">
              {publishStatus?.current_task_id ? <Button type="link" onClick={() => navigate(`/task/${publishStatus.current_task_id}`)}>任务 #{publishStatus.current_task_id}</Button> : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Shadow Read">
              {(publishStatus?.publish_pool_shadow_read ?? scheduleConfig?.publish_pool_shadow_read) ? '开启' : '关闭'}
            </Descriptions.Item>
            <Descriptions.Item label="Kill Switch">
              {(publishStatus?.publish_pool_kill_switch ?? scheduleConfig?.publish_pool_kill_switch) ? '开启' : '关闭'}
            </Descriptions.Item>
            <Descriptions.Item label="当前发布池项">
              {currentPoolItem ? (
                <Space wrap>
                  <Tag color={publishPoolStatusMeta[currentPoolItem.status].color}>{publishPoolStatusMeta[currentPoolItem.status].label}</Tag>
                  <Tag color={isPoolVersionAligned(currentPoolItem) ? 'success' : 'warning'}>版本 #{currentPoolItem.creative_version_id}</Tag>
                </Space>
              ) : '当前版本暂未进入发布池'}
            </Descriptions.Item>
            <Descriptions.Item label="Pool Item ID">{currentPoolItem ? `#${currentPoolItem.id}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="最近失效记录" span={2}>
              {latestInvalidatedPoolItem ? (
                <Space direction="vertical" size={4}>
                  <Text>Pool #{latestInvalidatedPoolItem.id} / 版本 #{latestInvalidatedPoolItem.creative_version_id}</Text>
                  <Text type="secondary">失效于 {formatCreativeTimestamp(latestInvalidatedPoolItem.invalidated_at ?? latestInvalidatedPoolItem.updated_at)}</Text>
                  <Text type="secondary">原因：{latestInvalidatedPoolItem.invalidation_reason ?? '未记录'}</Text>
                </Space>
              ) : '暂无失效记录'}
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
          {activePoolItems.length === 0 && invalidatedPoolItems.length === 0 ? (
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
              {shadowDiffReasons.length > 0 ? shadowDiffReasons.map((reason) => <Tag key={reason}>{reason}</Tag>) : <Tag>无差异原因</Tag>}
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
      onBack={() => navigate('/creative/workbench')}
      extra={[
        primaryTaskId ? <Button key="task-detail" onClick={() => navigate(`/task/${primaryTaskId}`)} data-testid="creative-open-task-diagnostics">查看任务诊断</Button> : null,
        currentVersion ? <Button key="ai-clip" onClick={openAiClipWorkflow} data-testid="creative-open-ai-clip">AIClip 工作流</Button> : null,
        currentVersion ? <Button key="review" type="primary" data-testid="creative-open-review" onClick={() => setDrawerOpen(true)}>审核当前版本</Button> : null,
      ].filter(Boolean)}
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        {creative.generation_error_msg ? (
          <Alert type="warning" showIcon message="当前发布链路存在失败记录" description={`最近失败于 ${formatCreativeTimestamp(creative.generation_failed_at)}，错误：${creative.generation_error_msg}`} />
        ) : null}

        <Card title="业务概览">
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="作品编号">{creative.creative_no}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusMeta.color}>{statusMeta.label}</Tag></Descriptions.Item>
            <Descriptions.Item label="当前版本 ID">{creative.current_version_id ?? '-'}</Descriptions.Item>
            <Descriptions.Item label="最近更新时间">{formatCreativeTimestamp(creative.updated_at)}</Descriptions.Item>
          </Descriptions>
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            这里优先展示运营决策所需的信息；发布链路、调度与 Cutover 诊断请展开下方高级诊断查看。
          </Paragraph>
        </Card>

        <Flex gap={16} wrap="wrap" align="stretch">
          <Card title="当前版本" style={{ flex: 1, minWidth: 320 }}>
            {creative.current_version ? (
              <Descriptions bordered size="small" column={2}>
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
                {effectiveCheck.note ? <Paragraph style={{ marginBottom: 0 }}>{effectiveCheck.note}</Paragraph> : <Paragraph type="secondary" style={{ marginBottom: 0 }}>未填写审核备注</Paragraph>}
                {creative.review_summary?.total_checks ? <Text type="secondary">累计审核记录 {creative.review_summary.total_checks} 条</Text> : null}
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

        <Card title="任务诊断入口">
          {diagnosticTaskIds.length > 0 ? (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                任务页用于查看执行、重试、发布链路与排障细节；业务判断仍以当前作品详情为准。
              </Paragraph>
              <Space wrap>
                {diagnosticTaskIds.map((taskId) => <Button key={taskId} onClick={() => navigate(`/task/${taskId}`)} data-testid={`creative-open-task-${taskId}`}>任务 #{taskId}</Button>)}
                <Button onClick={() => navigate('/task/list')}>查看任务列表</Button>
              </Space>
            </Space>
          ) : <Empty description="当前没有关联任务" />}
        </Card>

        <Card title="高级诊断" extra={<Text type="secondary">展开查看发布池 / 调度 / Cutover 差异</Text>}>
          <Paragraph type="secondary">
            以下信息用于排查发布池、调度切换与 Cutover 问题，不作为作品业务状态的首要阅读区。
          </Paragraph>
          <Collapse items={diagnosticsPanels} />
        </Card>
      </Space>

      <CheckDrawer creativeId={creativeId} open={drawerOpen} version={currentVersion} onClose={() => setDrawerOpen(false)} />

      <Drawer title="AIClip 工作流" open={aiClipOpen} width={720} onClose={closeAiClipWorkflow} destroyOnClose>
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
