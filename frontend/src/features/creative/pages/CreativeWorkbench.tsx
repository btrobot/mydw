import { ArrowRightOutlined } from '@ant-design/icons'
import { PageContainer } from '@ant-design/pro-components'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Flex,
  List,
  Segmented,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd'

import CreativeEmptyState from '../components/CreativeEmptyState'
import {
  useCreatives,
  usePublishPoolItems,
  usePublishStatus,
  useScheduleConfig,
} from '../hooks/useCreatives'
import type { PublishPoolItem } from '../types/creative'
import {
  formatCreativeTimestamp,
  creativeStatusMeta,
  isPoolVersionAligned,
  publishPoolStatusMeta,
  publishSchedulerModeMeta,
  publishRuntimeStatusMeta,
} from '../types/creative'

const { Paragraph, Text, Title } = Typography

type WorkbenchPoolFilter = 'all' | 'pool' | 'unpooled'

const WORKBENCH_STATUS_LABELS = {
  PENDING_INPUT: 'Pending input',
  WAITING_REVIEW: 'Waiting review',
  APPROVED: 'Approved',
  REWORK_REQUIRED: 'Rework required',
  REJECTED: 'Rejected',
} as const

const WORKBENCH_POOL_STATUS_LABELS = {
  active: 'In publish pool',
  invalidated: 'Invalidated',
} as const

const WORKBENCH_SCHEDULER_MODE_LABELS = {
  task: 'Task mode',
  pool: 'Pool mode',
} as const

const WORKBENCH_RUNTIME_LABELS = {
  idle: 'Idle',
  running: 'Running',
  paused: 'Paused',
} as const

export default function CreativeWorkbench() {
  const navigate = useNavigate()
  const { data, isLoading } = useCreatives()
  const { data: poolData, isLoading: poolLoading } = usePublishPoolItems({
    limit: 200,
    status: 'active',
  })
  const { data: publishStatus } = usePublishStatus()
  const { data: scheduleConfig } = useScheduleConfig()
  const [poolFilter, setPoolFilter] = useState<WorkbenchPoolFilter>('all')

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const activePoolItems = poolData?.items ?? []

  const poolByCreativeId = useMemo(
    () => new Map<number, PublishPoolItem>(activePoolItems.map((item) => [item.creative_item_id, item])),
    [activePoolItems],
  )

  const filteredItems = useMemo(() => {
    if (poolFilter === 'pool') {
      return items.filter((item) => poolByCreativeId.has(item.id))
    }

    if (poolFilter === 'unpooled') {
      return items.filter((item) => !poolByCreativeId.has(item.id))
    }

    return items
  }, [items, poolByCreativeId, poolFilter])

  const alignedPoolCount = useMemo(
    () => activePoolItems.filter((item) => isPoolVersionAligned(item)).length,
    [activePoolItems],
  )

  const schedulerMode = publishStatus?.scheduler_mode ?? scheduleConfig?.publish_scheduler_mode
  const effectiveSchedulerMode = publishStatus?.effective_scheduler_mode ?? schedulerMode
  const runtimeStatus = publishStatus?.status

  if (isLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  return (
    <PageContainer
      title="Creative workbench"
      subTitle="Default daily entry for creative operations, review, and publish diagnostics"
      extra={[
        <Button
          key="dashboard"
          onClick={() => navigate('/dashboard')}
          data-testid="creative-workbench-open-dashboard"
        >
          Open runtime dashboard
        </Button>,
        <Button
          key="tasks"
          onClick={() => navigate('/task/list')}
          data-testid="creative-workbench-open-task-list"
        >
          Open task diagnostics
        </Button>,
      ]}
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Alert
          type="info"
          showIcon
          message="Creative workbench is the default main entry"
          description="Use this page for day-to-day creative work: open detail pages, review current versions, enter AIClip workflow, and inspect publish readiness. Task pages remain diagnostics surfaces, and the runtime dashboard stays available as a secondary view."
          data-testid="creative-workbench-main-entry-banner"
        />

        <Card data-testid="creative-workbench-publish-summary">
          <Flex wrap gap={24}>
            <Statistic title="Creatives" value={total} />
            <Statistic title="Active pool items" value={poolData?.total ?? 0} loading={poolLoading} />
            <Statistic title="Version-aligned pool items" value={alignedPoolCount} loading={poolLoading} />
            <Statistic title="Publish failures" value={publishStatus?.total_failed ?? 0} />
          </Flex>

          <Space wrap size={[8, 8]} style={{ marginTop: 16 }}>
            <Tag
              color={schedulerMode ? publishSchedulerModeMeta[schedulerMode].color : 'default'}
              data-testid="creative-workbench-scheduler-mode"
            >
              Configured mode: {schedulerMode ? WORKBENCH_SCHEDULER_MODE_LABELS[schedulerMode] : '-'}
            </Tag>
            <Tag
              color={effectiveSchedulerMode ? publishSchedulerModeMeta[effectiveSchedulerMode].color : 'default'}
              data-testid="creative-workbench-effective-mode"
            >
              Effective mode: {effectiveSchedulerMode ? WORKBENCH_SCHEDULER_MODE_LABELS[effectiveSchedulerMode] : '-'}
            </Tag>
            <Tag
              color={runtimeStatus ? publishRuntimeStatusMeta[runtimeStatus].color : 'default'}
              data-testid="creative-workbench-runtime-status"
            >
              Runtime: {runtimeStatus ? WORKBENCH_RUNTIME_LABELS[runtimeStatus] : '-'}
            </Tag>
            <Tag data-testid="creative-workbench-shadow-read">
              Shadow read: {publishStatus?.publish_pool_shadow_read ? 'ON' : 'OFF'}
            </Tag>
            <Tag data-testid="creative-workbench-kill-switch">
              Kill switch: {publishStatus?.publish_pool_kill_switch ? 'ON' : 'OFF'}
            </Tag>
          </Space>

          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            Filter the list below to inspect in-pool and unpooled creatives. Open each detail page to review versions, checks, AIClip workflow access, and task diagnostics round-trips without leaving the creative-first flow.
          </Paragraph>
        </Card>

        <Card
          size="small"
          title="Pool visibility filter"
          data-testid="creative-workbench-pool-filter"
          extra={(
            <Segmented
              options={[
                { label: 'All creatives', value: 'all' },
                { label: 'In pool', value: 'pool' },
                { label: 'Not in pool', value: 'unpooled' },
              ]}
              value={poolFilter}
              onChange={(value) => setPoolFilter(value as WorkbenchPoolFilter)}
            />
          )}
        >
          <Text type="secondary">
            This filter is read-only. It helps verify creative status, current version alignment, and publish-pool projection readiness before you inspect a specific creative.
          </Text>
        </Card>

        {items.length === 0 ? (
          <Card>
            <CreativeEmptyState onOpenTaskList={() => navigate('/task/list')} />
          </Card>
        ) : (
          <List
            grid={{ gutter: 16, xs: 1, sm: 1, md: 2, xl: 3 }}
            dataSource={filteredItems}
            renderItem={(item) => {
              const statusMeta = creativeStatusMeta[item.status]
              const poolItem = poolByCreativeId.get(item.id)
              const poolAligned = poolItem ? isPoolVersionAligned(poolItem) : false

              return (
                <List.Item key={item.id}>
                  <Card
                    title={item.title ?? item.creative_no}
                    extra={(
                      <Button
                        type="link"
                        icon={<ArrowRightOutlined />}
                        onClick={() => navigate(`/creative/${item.id}`)}
                        data-testid={`creative-workbench-open-detail-${item.id}`}
                      >
                        View detail
                      </Button>
                    )}
                  >
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                      <div>
                        <Text type="secondary">Creative number</Text>
                        <Title level={5} style={{ marginTop: 4, marginBottom: 0 }}>
                          {item.creative_no}
                        </Title>
                      </div>

                      <Space wrap>
                        <Tag color={statusMeta.color}>{WORKBENCH_STATUS_LABELS[item.status]}</Tag>
                        <Tag>Current version #{item.current_version_id ?? '-'}</Tag>
                      </Space>

                      <Space wrap>
                        <Button
                          type="primary"
                          onClick={() => navigate(`/creative/${item.id}?tool=ai-clip`)}
                          disabled={!item.current_version_id}
                          data-testid={`creative-workbench-ai-clip-${item.id}`}
                        >
                          AIClip workflow
                        </Button>
                      </Space>

                      <Space wrap data-testid={`creative-workbench-pool-state-${item.id}`}>
                        {poolItem ? (
                          <>
                            <Tag color={publishPoolStatusMeta[poolItem.status].color}>
                              {WORKBENCH_POOL_STATUS_LABELS[poolItem.status]}
                            </Tag>
                            <Tag color={poolAligned ? 'success' : 'warning'}>
                              Pool version #{poolItem.creative_version_id}
                            </Tag>
                            <Tag color={poolAligned ? 'success' : 'warning'}>
                              {poolAligned ? 'Aligned with current version' : 'Not aligned with current version'}
                            </Tag>
                          </>
                        ) : (
                          <Tag>Not in publish pool</Tag>
                        )}
                      </Space>

                      {poolItem ? (
                        <Text type="secondary">Pool item #{poolItem.id}</Text>
                      ) : null}

                      {item.generation_error_msg ? (
                        <Alert
                          type="warning"
                          showIcon
                          message="Latest generation writeback failed"
                          description={item.generation_error_msg}
                        />
                      ) : null}

                      <Text type="secondary">
                        Updated at: {formatCreativeTimestamp(item.updated_at)}
                      </Text>
                    </Space>
                  </Card>
                </List.Item>
              )
            }}
          />
        )}
      </Space>
    </PageContainer>
  )
}
