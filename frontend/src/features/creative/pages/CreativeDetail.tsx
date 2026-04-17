import { PageContainer } from '@ant-design/pro-components'
import { useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
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

import CheckDrawer from '../components/CheckDrawer'
import AIClipWorkflowPanel from '../components/AIClipWorkflowPanel'
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

  const primaryTaskId = useMemo(
    () => creative?.linked_task_ids?.[0],
    [creative?.linked_task_ids],
  )

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
  const effectiveCheckMeta = effectiveCheck
    ? creativeReviewConclusionMeta[effectiveCheck.conclusion]
    : null

  const schedulerMode = publishStatus?.scheduler_mode ?? scheduleConfig?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatus?.effective_scheduler_mode ?? schedulerMode
  const shadowDiff = publishStatus?.scheduler_shadow_diff
  const shadowDiffReasons = formatShadowDiffReasons(shadowDiff)
  const shadowDiffDiffers = getShadowDiffFlag(shadowDiff)
  const diagnosticsUnavailable = publishStatusError || scheduleConfigError || activePoolError || invalidatedPoolError

  if (isLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (!creative || isError || !statusMeta) {
    return (
      <PageContainer title="作品不存在" onBack={() => navigate('/creative/workbench')}>
        <Empty description="未找到对应作品，或该作品尚未进入当前工作台。" />
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title={creative.title ?? creative.creative_no}
      subTitle={creative.creative_no}
      onBack={() => navigate('/creative/workbench')}
      extra={[
        primaryTaskId ? (
          <Button
            key="task-detail"
            onClick={() => navigate(`/task/${primaryTaskId}`)}
            data-testid="creative-open-task-diagnostics"
          >
            查看关联任务
          </Button>
        ) : null,
        currentVersion ? (
          <Button
            key="ai-clip"
            onClick={openAiClipWorkflow}
            data-testid="creative-open-ai-clip"
          >
            AIClip workflow
          </Button>
        ) : null,
        currentVersion ? (
          <Button
            key="review"
            type="primary"
            data-testid="creative-open-review"
            onClick={() => setDrawerOpen(true)}
          >
            审核当前版本
          </Button>
        ) : null,
        <Button key="task-list" onClick={() => navigate('/task/list')}>
          返回任务列表
        </Button>,
      ].filter(Boolean)}
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Alert
          type="info"
          showIcon
          message="Phase C：版本、发布池与 cutover 诊断聚合页"
          description="当前页面承担当前版本审核、发布池候选可见性与 scheduler cutover 诊断，但仍不提供直接绕过 scheduler 的发布入口。"
        />

        {diagnosticsUnavailable ? (
          <Alert
            type="warning"
            showIcon
            message="部分发布诊断暂不可用"
            description="publish status / schedule config / publish pool 读投影至少有一个接口未返回，页面会继续显示已拿到的 Creative 与任务基线。"
          />
        ) : null}

        {creative.generation_error_msg ? (
          <Alert
            type="warning"
            showIcon
            message="最近一次生成回写失败"
            description={`失败时间：${formatCreativeTimestamp(creative.generation_failed_at)}；原因：${creative.generation_error_msg}`}
          />
        ) : null}

        <Card title="作品概览">
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="作品编号">{creative.creative_no}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusMeta.color}>{statusMeta.label}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前版本 ID">
              {creative.current_version_id ?? '-'}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {formatCreativeTimestamp(creative.updated_at)}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="Phase C 发布诊断" data-testid="creative-publish-diagnostics">
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="配置模式">
              <Tag color={schedulerMode ? publishSchedulerModeMeta[schedulerMode].color : 'default'}>
                {formatModeLabel(schedulerMode)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="生效模式">
              <Tag
                color={effectiveSchedulerMode ? publishSchedulerModeMeta[effectiveSchedulerMode].color : 'default'}
              >
                {formatModeLabel(effectiveSchedulerMode)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Runtime 状态">
              <Tag
                color={publishStatus?.status ? publishRuntimeStatusMeta[publishStatus.status].color : 'default'}
              >
                {formatRuntimeStatusLabel(publishStatus?.status)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="当前执行任务">
              {publishStatus?.current_task_id ? (
                <Button type="link" onClick={() => navigate(`/task/${publishStatus.current_task_id}`)}>
                  Task #{publishStatus.current_task_id}
                </Button>
              ) : (
                '-'
              )}
            </Descriptions.Item>
            <Descriptions.Item label="Shadow Read">
              {publishStatus?.publish_pool_shadow_read ?? scheduleConfig?.publish_pool_shadow_read ? 'ON' : 'OFF'}
            </Descriptions.Item>
            <Descriptions.Item label="Kill Switch">
              {publishStatus?.publish_pool_kill_switch ?? scheduleConfig?.publish_pool_kill_switch ? 'ON' : 'OFF'}
            </Descriptions.Item>
            <Descriptions.Item label="池中候选状态">
              {currentPoolItem ? (
                <Space wrap>
                  <Tag color={publishPoolStatusMeta[currentPoolItem.status].color}>
                    {publishPoolStatusMeta[currentPoolItem.status].label}
                  </Tag>
                  <Tag color={isPoolVersionAligned(currentPoolItem) ? 'success' : 'warning'}>
                    池版本 #{currentPoolItem.creative_version_id}
                  </Tag>
                </Space>
              ) : (
                '当前版本未命中 active pool item'
              )}
            </Descriptions.Item>
            <Descriptions.Item label="Pool Item ID">
              {currentPoolItem ? `#${currentPoolItem.id}` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="最新失效记录" span={2}>
              {latestInvalidatedPoolItem ? (
                <Space direction="vertical" size={4}>
                  <Text>
                    Pool #{latestInvalidatedPoolItem.id} / 版本 #{latestInvalidatedPoolItem.creative_version_id}
                  </Text>
                  <Text type="secondary">
                    失效时间：{formatCreativeTimestamp(latestInvalidatedPoolItem.invalidated_at ?? latestInvalidatedPoolItem.updated_at)}
                  </Text>
                  <Text type="secondary">
                    原因：{latestInvalidatedPoolItem.invalidation_reason ?? '未提供'}
                  </Text>
                </Space>
              ) : (
                '暂无失效记录'
              )}
            </Descriptions.Item>
          </Descriptions>

          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            如需追查执行链，可继续通过下方任务链接进入 TaskDetail；Creative 详情页仅负责对齐当前版本、pool 投影与 cutover 只读信息。
          </Paragraph>
        </Card>

        <Card title="发布池投影" data-testid="creative-publish-pool-card">
          {activePoolItems.length === 0 && invalidatedPoolItems.length === 0 ? (
            <Empty description="当前作品暂无发布池记录" />
          ) : (
            <List
              dataSource={[...activePoolItems, ...invalidatedPoolItems]}
              renderItem={(item) => {
                const aligned = isPoolVersionAligned(item)

                return (
                  <List.Item key={`${item.status}-${item.id}`} data-testid={`creative-pool-item-${item.id}`}>
                    <Space direction="vertical" size={6} style={{ width: '100%' }}>
                      <Space wrap>
                        <Tag color={publishPoolStatusMeta[item.status].color}>
                          {publishPoolStatusMeta[item.status].label}
                        </Tag>
                        <Tag color={aligned ? 'success' : 'warning'}>
                          版本 #{item.creative_version_id}
                        </Tag>
                        <Tag color={aligned ? 'success' : 'warning'}>
                          {aligned ? '与当前版本一致' : '与当前版本不一致'}
                        </Tag>
                        <Tag>Pool #{item.id}</Tag>
                      </Space>
                      <Text type="secondary">
                        创建时间：{formatCreativeTimestamp(item.created_at)}；更新时间：{formatCreativeTimestamp(item.updated_at)}
                      </Text>
                      {item.invalidation_reason ? (
                        <Text type="secondary">失效原因：{item.invalidation_reason}</Text>
                      ) : null}
                    </Space>
                  </List.Item>
                )
              }}
            />
          )}
        </Card>

        {shadowDiff ? (
          <Card title="Cutover Shadow Diff" data-testid="creative-shadow-diff">
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Space wrap>
                <Tag color={shadowDiffDiffers ? 'warning' : 'success'}>
                  {shadowDiffDiffers ? '候选存在差异' : '候选一致'}
                </Tag>
                {shadowDiffReasons.length > 0
                  ? shadowDiffReasons.map((reason) => <Tag key={reason}>{reason}</Tag>)
                  : <Tag>无额外差异原因</Tag>}
              </Space>
              <pre
                style={{
                  margin: 0,
                  padding: 12,
                  background: '#fafafa',
                  borderRadius: 8,
                  overflow: 'auto',
                }}
              >
                {formatShadowDiffJson(shadowDiff)}
              </pre>
            </Space>
          </Card>
        ) : null}

        <Card title="当前版本">
          {creative.current_version ? (
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="版本 ID">
                {creative.current_version.id}
              </Descriptions.Item>
              <Descriptions.Item label="版本号">
                {getVersionLabel(creative.current_version.version_no)}
              </Descriptions.Item>
              <Descriptions.Item label="版本标题" span={2}>
                {creative.current_version.title ?? '未命名版本'}
              </Descriptions.Item>
              <Descriptions.Item label="父版本 ID">
                {creative.current_version.parent_version_id ?? '-'}
              </Descriptions.Item>
              <Descriptions.Item label="PackageRecord ID">
                {creative.current_version.package_record_id ?? '-'}
              </Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="当前作品还没有版本投影。" />
          )}
        </Card>

        <Card title="当前有效审核结论" data-testid="creative-review-summary">
          {effectiveCheck && effectiveCheckMeta ? (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Space wrap>
                <Tag color={effectiveCheckMeta.color}>{formatCheckConclusion(effectiveCheck)}</Tag>
                <Tag color="processing">
                  生效于 {getVersionLabel(creative.review_summary?.current_version_id)}
                </Tag>
              </Space>
              <Text type="secondary">
                最后更新时间：{formatCreativeTimestamp(effectiveCheck.updated_at)}
              </Text>
              {effectiveCheck.note ? (
                <Paragraph style={{ marginBottom: 0 }}>{effectiveCheck.note}</Paragraph>
              ) : (
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  暂无补充说明。
                </Paragraph>
              )}
              {creative.review_summary?.total_checks ? (
                <Text type="secondary">
                  历史审核记录共 {creative.review_summary.total_checks} 条。
                </Text>
              ) : null}
            </Space>
          ) : (
            <Alert
              type="info"
              showIcon
              message="当前版本还没有有效审核结论"
              description="请仅对当前版本执行通过 / 返工 / 驳回操作；历史版本的审核结果会被保留，但不会继续作为当前业务结论。"
            />
          )}
        </Card>

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

        <Card title="关联任务（诊断入口）">
          {diagnosticTaskIds.length > 0 ? (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                Task 仍用于查看执行链路与诊断信息，不作为当前作品业务真相来源；若 cutover 后出现异常，请优先从 TaskDetail 回溯发布失败链。
              </Paragraph>
              <Space wrap>
                {diagnosticTaskIds.map((taskId) => (
                  <Button
                    key={taskId}
                    onClick={() => navigate(`/task/${taskId}`)}
                    data-testid={`creative-open-task-${taskId}`}
                  >
                    打开任务 #{taskId}
                  </Button>
                ))}
              </Space>
            </Space>
          ) : (
            <Empty description="当前作品还没有关联任务。" />
          )}
        </Card>
      </Space>

      <CheckDrawer
        creativeId={creativeId}
        open={drawerOpen}
        version={currentVersion}
        onClose={() => setDrawerOpen(false)}
      />

      <Drawer
        title="AIClip workflow"
        open={aiClipOpen}
        width={720}
        onClose={closeAiClipWorkflow}
        destroyOnClose
      >
        <div data-testid="creative-ai-clip-drawer">
          <AIClipWorkflowPanel
            creativeContext={creativeId && currentVersion ? {
              creativeId,
              creativeTitle: creative.title,
              sourceVersionId: currentVersion.id,
              sourceVersionLabel: getVersionLabel(currentVersion.version_no),
              onSubmitted: () => {
                closeAiClipWorkflow()
              },
            } : null}
          />
        </div>
      </Drawer>
    </PageContainer>
  )
}
