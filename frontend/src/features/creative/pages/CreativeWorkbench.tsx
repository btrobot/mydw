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
  creativeStatusMeta,
  formatCreativeTimestamp,
  formatModeLabel,
  formatRuntimeStatusLabel,
  isPoolVersionAligned,
  publishPoolStatusMeta,
  publishRuntimeStatusMeta,
  publishSchedulerModeMeta,
} from '../types/creative'

const { Paragraph, Text, Title } = Typography

type WorkbenchPoolFilter = 'all' | 'pool' | 'unpooled'

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
      title="作品工作台"
      subTitle="Phase C：发布池可见性与 cutover 诊断"
      extra={[
        <Button key="tasks" onClick={() => navigate('/task/list')}>
          查看任务列表
        </Button>,
      ]}
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Alert
          type="info"
          showIcon
          message="Phase C 只读诊断入口"
          description="工作台现在会投影发布池候选、scheduler 模式与 cutover 诊断，但仍不提供直接绕过 scheduler 的发布按钮。"
        />

        <Card data-testid="creative-workbench-publish-summary">
          <Flex wrap gap={24}>
            <Statistic title="作品总数" value={total} />
            <Statistic title="池中候选" value={poolData?.total ?? 0} loading={poolLoading} />
            <Statistic title="版本对齐候选" value={alignedPoolCount} loading={poolLoading} />
            <Statistic title="发布失败累计" value={publishStatus?.total_failed ?? 0} />
          </Flex>

          <Space wrap size={[8, 8]} style={{ marginTop: 16 }}>
            <Tag
              color={schedulerMode ? publishSchedulerModeMeta[schedulerMode].color : 'default'}
              data-testid="creative-workbench-scheduler-mode"
            >
              配置模式：{formatModeLabel(schedulerMode)}
            </Tag>
            <Tag
              color={effectiveSchedulerMode ? publishSchedulerModeMeta[effectiveSchedulerMode].color : 'default'}
              data-testid="creative-workbench-effective-mode"
            >
              生效模式：{formatModeLabel(effectiveSchedulerMode)}
            </Tag>
            <Tag
              color={runtimeStatus ? publishRuntimeStatusMeta[runtimeStatus].color : 'default'}
              data-testid="creative-workbench-runtime-status"
            >
              Runtime：{formatRuntimeStatusLabel(runtimeStatus)}
            </Tag>
            <Tag data-testid="creative-workbench-shadow-read">
              Shadow Read：{publishStatus?.publish_pool_shadow_read ? 'ON' : 'OFF'}
            </Tag>
            <Tag data-testid="creative-workbench-kill-switch">
              Kill Switch：{publishStatus?.publish_pool_kill_switch ? 'ON' : 'OFF'}
            </Tag>
          </Space>

          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            可通过下方筛选查看已入池候选与未入池作品；详情页继续承担版本、发布链与任务诊断聚合视图。
          </Paragraph>
        </Card>

        <Card
          size="small"
          title="候选筛选"
          data-testid="creative-workbench-pool-filter"
          extra={(
            <Segmented
              options={[
                { label: '全部作品', value: 'all' },
                { label: '池中候选', value: 'pool' },
                { label: '未入池', value: 'unpooled' },
              ]}
              value={poolFilter}
              onChange={(value) => setPoolFilter(value as WorkbenchPoolFilter)}
            />
          )}
        >
          <Text type="secondary">
            当前筛选不会触发发布动作，只用于核对作品状态、当前版本与 publish pool 投影是否一致。
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
                      >
                        查看详情
                      </Button>
                    )}
                  >
                    <Space direction="vertical" size={12} style={{ width: '100%' }}>
                      <div>
                        <Text type="secondary">作品编号</Text>
                        <Title level={5} style={{ marginTop: 4, marginBottom: 0 }}>
                          {item.creative_no}
                        </Title>
                      </div>

                      <Space wrap>
                        <Tag color={statusMeta.color}>{statusMeta.label}</Tag>
                        <Tag>当前版本 #{item.current_version_id ?? '-'}</Tag>
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
                              {publishPoolStatusMeta[poolItem.status].label}
                            </Tag>
                            <Tag color={poolAligned ? 'success' : 'warning'}>
                              池版本 #{poolItem.creative_version_id}
                            </Tag>
                            <Tag color={poolAligned ? 'success' : 'warning'}>
                              {poolAligned ? '与当前版本一致' : '与当前版本不一致'}
                            </Tag>
                          </>
                        ) : (
                          <Tag>未在发布池</Tag>
                        )}
                      </Space>

                      {poolItem ? (
                        <Text type="secondary">Pool Item #{poolItem.id}</Text>
                      ) : null}

                      {item.generation_error_msg ? (
                        <Alert
                          type="warning"
                          showIcon
                          message="最近一次生成失败"
                          description={item.generation_error_msg}
                        />
                      ) : null}

                      <Text type="secondary">
                        更新时间：{formatCreativeTimestamp(item.updated_at)}
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
