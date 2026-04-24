import { useState, type ReactNode } from 'react'
import type {
  CreativeCurrentSelectionFieldResponse,
  CreativeReadinessState,
  CreativeSelectionState,
  CreativeZoneMaterialCandidateResponse,
} from '@/api'
import { Button, Card, Empty, Flex, List, Space, Tag, Typography } from 'antd'

import type { CreativeDetail } from '../../types/creative'
import {
  formatCreativeDurationSeconds,
  formatCreativeText,
  formatCreativeTimestamp,
  getVersionLabel,
} from '../../types/creative'
import type { CreativeDetailProjectionModel } from './projection'

const { Paragraph, Text, Title } = Typography

const pageModeMeta: Record<
  CreativeDetailProjectionModel['pageMode'],
  { label: string; color: string; description: string }
> = {
  definition: {
    label: '定义阶段',
    color: 'blue',
    description: '先明确当前入选内容，再进入生成。',
  },
  result_pending_confirm: {
    label: '结果待确认',
    color: 'gold',
    description: '当前已有结果，先确认是否沿用当前版本。',
  },
  published_followup: {
    label: '发布跟进',
    color: 'green',
    description: '当前重点转为结果、版本与发布跟进。',
  },
}

const readinessMeta: Record<
  CreativeReadinessState,
  { label: string; color: string; description: string }
> = {
  not_started: {
    label: '未开始',
    color: 'default',
    description: '核心输入还没有形成。',
  },
  partial: {
    label: '部分就绪',
    color: 'orange',
    description: '已有部分输入，但距离生成还差关键项。',
  },
  ready: {
    label: '可生成',
    color: 'success',
    description: '当前作品已满足提交生成条件。',
  },
  result_pending_confirm: {
    label: '结果待确认',
    color: 'gold',
    description: '先确认当前结果，再决定是否继续改定义。',
  },
  published_followup: {
    label: '发布跟进',
    color: 'green',
    description: '当前重点是版本沿用与发布承接。',
  },
}

const selectionStateMeta: Record<
  CreativeSelectionState,
  { label: string; color: string }
> = {
  missing: {
    label: '缺失',
    color: 'default',
  },
  defined: {
    label: '已定义',
    color: 'success',
  },
  detached: {
    label: '已脱钩',
    color: 'warning',
  },
}

type CreativeDetailHeroCardProps = {
  creative: CreativeDetail
  projection: CreativeDetailProjectionModel
  statusMeta: { color: string; label: string }
  modeMeta: { label: string; color: string }
  activeInputItemCount: number
  summaryTitle: string
  summaryLead: string
  summarySupportingText?: string
  primaryAction: {
    label: string
    onClick: () => void
    disabled?: boolean
    loading?: boolean
    testId: string
  }
  secondaryActions?: Array<{
    key: string
    label: string
    onClick: () => void
    disabled?: boolean
    loading?: boolean
    testId: string
  }>
}

export function CreativeDetailHeroCard({
  creative,
  projection,
  statusMeta,
  modeMeta,
  activeInputItemCount,
  summaryTitle,
  summaryLead,
  summarySupportingText,
  primaryAction,
  secondaryActions = [],
}: CreativeDetailHeroCardProps) {
  const pageMode = pageModeMeta[projection.pageMode]
  const readinessState = projection.readiness.state ?? 'not_started'
  const readiness = readinessMeta[readinessState]
  const missingFields = projection.readiness.missing_fields ?? []
  const currentVersionLabel = creative.current_version
    ? getVersionLabel(creative.current_version.version_no)
    : '暂无版本'

  return (
    <Card data-testid="creative-detail-shell-hero">
      <Flex vertical gap={16}>
        <Flex justify="space-between" align="start" wrap="wrap" gap={16}>
          <Space direction="vertical" size={4}>
            <Text type="secondary">CreativeDetail / 页面壳重构首屏</Text>
            <Title level={3} style={{ margin: 0 }}>
              {creative.title ?? creative.creative_no}
            </Title>
            <Space wrap>
              <Tag color={statusMeta.color}>{statusMeta.label}</Tag>
              <Tag color={pageMode.color}>{pageMode.label}</Tag>
              <Tag color={readiness.color}>{readiness.label}</Tag>
              <Tag>当前版本：{currentVersionLabel}</Tag>
              <Tag>入选媒体：{activeInputItemCount}</Tag>
            </Space>
          </Space>

          <Space wrap>
            {secondaryActions.map((action) => (
              <Button
                key={action.key}
                loading={action.loading}
                disabled={action.disabled}
                onClick={action.onClick}
                data-testid={action.testId}
              >
                {action.label}
              </Button>
            ))}
            <Button
              type="primary"
              loading={primaryAction.loading}
              disabled={primaryAction.disabled}
              onClick={primaryAction.onClick}
              data-testid={primaryAction.testId}
            >
              {primaryAction.label}
            </Button>
          </Space>
        </Flex>

        <Flex wrap gap={12}>
          <Tag color={readiness.color}>当前状态：{readiness.label}</Tag>
          <Tag color={modeMeta.color}>当前模式：{modeMeta.label}</Tag>
          <Text type="secondary">最近更新：{formatCreativeTimestamp(creative.updated_at)}</Text>
          <Text type="secondary">缺失项：{missingFields.length}</Text>
        </Flex>

        <Card
          size="small"
          type="inner"
          title={summaryTitle}
        >
          <Space direction="vertical" size={8} style={{ width: '100%' }}>
            <Text>{summaryLead}</Text>
            <Text type="secondary">{pageMode.description}</Text>
            {summarySupportingText ? (
              <Text type="secondary">{summarySupportingText}</Text>
            ) : projection.readiness.next_action_hint ? (
              <Text type="secondary">{projection.readiness.next_action_hint}</Text>
            ) : null}
            {missingFields.length > 0 ? (
              <Space wrap>
                {missingFields.map((field) => (
                  <Tag key={field}>{field}</Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">当前没有阻断生成的缺失项。</Text>
            )}
          </Space>
        </Card>
      </Flex>
    </Card>
  )
}

type CreativeCurrentSelectionSectionProps = {
  projection: CreativeDetailProjectionModel
  productNameEditor?: ReactNode
  copywritingEditor?: ReactNode
  productNameActions?: ReactNode
  coverActions?: ReactNode
  copywritingActions?: ReactNode
  audioActions?: ReactNode
  renderVideoActions?: (video: CreativeCurrentSelectionFieldResponse, index: number) => ReactNode
  renderVideoFooter?: (video: CreativeCurrentSelectionFieldResponse, index: number) => ReactNode
  getVideoWarnings?: (video: CreativeCurrentSelectionFieldResponse, index: number) => ReactNode
  onVideoDrop?: (fromIndex: number, toIndex: number) => void
}

const getSelectionStatus = (field?: CreativeCurrentSelectionFieldResponse) =>
  selectionStateMeta[field?.state ?? 'missing']

function SelectionFieldCard({
  title,
  field,
  fallbackDescription,
  actions,
  footer,
}: {
  title: string
  field?: CreativeCurrentSelectionFieldResponse
  fallbackDescription: string
  actions?: ReactNode
  footer?: ReactNode
}) {
  const status = getSelectionStatus(field)
  const hasMainValue = Boolean(
    formatCreativeText(field?.value_text) !== '-'
    || formatCreativeText(field?.asset_name) !== '-',
  )

  return (
    <Card size="small" title={title} style={{ flex: 1, minWidth: 220 }}>
      <Space direction="vertical" size={8} style={{ width: '100%' }}>
        <Space wrap>
          <Tag color={status.color}>{status.label}</Tag>
          {field?.source_label ? <Tag>{field.source_label}</Tag> : null}
          {field?.detached ? <Tag color="warning">已脱钩</Tag> : null}
        </Space>
        {hasMainValue ? (
          <>
            {formatCreativeText(field?.value_text) !== '-' ? (
              <Text strong>{formatCreativeText(field?.value_text)}</Text>
            ) : null}
            {formatCreativeText(field?.asset_name) !== '-' ? (
              <Text>{formatCreativeText(field?.asset_name)}</Text>
            ) : null}
            {formatCreativeText(field?.asset_excerpt) !== '-' ? (
              <Text type="secondary">{formatCreativeText(field?.asset_excerpt)}</Text>
            ) : null}
            {field?.duration_seconds ? (
              <Text type="secondary">时长：{formatCreativeDurationSeconds(field.duration_seconds)}</Text>
            ) : null}
            {field?.adopted_from?.label ? (
              <Text type="secondary">来源：{field.adopted_from.label}</Text>
            ) : null}
          </>
        ) : (
          <Text type="secondary">{fallbackDescription}</Text>
        )}
        {actions ? <Space wrap>{actions}</Space> : null}
        {footer}
      </Space>
    </Card>
  )
}

export function CreativeCurrentSelectionSection({
  projection,
  productNameEditor,
  copywritingEditor,
  productNameActions,
  coverActions,
  copywritingActions,
  audioActions,
  renderVideoActions,
  renderVideoFooter,
  getVideoWarnings,
  onVideoDrop,
}: CreativeCurrentSelectionSectionProps) {
  const videos = projection.currentSelection.videos ?? []
  const [draggingVideoIndex, setDraggingVideoIndex] = useState<number | null>(null)

  return (
    <Card
      title="A. 当前入选区"
      extra={<Text type="secondary">当前真正会进入生成的内容</Text>}
      data-testid="creative-detail-current-selection"
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Paragraph type="secondary" style={{ marginBottom: 0 }}>
          先看最终采用了什么，再看这些内容从哪里来。当前入选区是本页首屏主角。
        </Paragraph>

        <Flex wrap gap={16} align="stretch">
          <SelectionFieldCard
            title="商品名称"
            field={projection.currentSelection.product_name}
            fallbackDescription="待定义当前商品名称。"
            actions={productNameActions}
            footer={productNameEditor}
          />
          <SelectionFieldCard
            title="封面"
            field={projection.currentSelection.cover}
            fallbackDescription="待从商品区或自由素材区选择封面。"
            actions={coverActions}
          />
          <SelectionFieldCard
            title="文案"
            field={projection.currentSelection.copywriting}
            fallbackDescription="待定义当前文案。"
            actions={copywritingActions}
            footer={copywritingEditor}
          />
          <SelectionFieldCard
            title="音频"
            field={projection.currentSelection.audio}
            fallbackDescription="待选择当前音频。"
            actions={audioActions}
          />
        </Flex>

        <Card size="small" type="inner" title={`视频集合（${videos.length}）`}>
          {videos.length > 0 ? (
            <List
              dataSource={videos}
              renderItem={(video, index) => {
                const status = getSelectionStatus(video)

                return (
                  <List.Item
                    key={`${video.asset_id ?? 'video'}-${video.sequence ?? video.instance_no ?? 0}`}
                    actions={renderVideoActions ? [renderVideoActions(video, index)] : undefined}
                  >
                    <div
                      draggable={Boolean(onVideoDrop)}
                      onDragStart={(event) => {
                        setDraggingVideoIndex(index)
                        event.dataTransfer.effectAllowed = 'move'
                        event.dataTransfer.setData('text/plain', String(index))
                      }}
                      onDragEnd={() => setDraggingVideoIndex(null)}
                      onDragOver={(event) => {
                        if (!onVideoDrop) {
                          return
                        }
                        event.preventDefault()
                      }}
                      onDrop={(event) => {
                        if (!onVideoDrop) {
                          return
                        }
                        event.preventDefault()
                        const droppedIndexText = event.dataTransfer.getData('text/plain')
                        const droppedIndex = droppedIndexText ? Number(droppedIndexText) : draggingVideoIndex
                        if (droppedIndex === null || Number.isNaN(droppedIndex)) {
                          return
                        }
                        onVideoDrop(droppedIndex, index)
                        setDraggingVideoIndex(null)
                      }}
                      data-testid={`creative-current-selection-video-card-${video.asset_id ?? 'unknown'}-${index}`}
                      style={{
                        width: '100%',
                        borderRadius: 8,
                        padding: 8,
                        border: draggingVideoIndex === index ? '1px dashed #1677ff' : '1px dashed transparent',
                        background: draggingVideoIndex === index ? '#f0f5ff' : 'transparent',
                        cursor: onVideoDrop ? 'grab' : 'default',
                      }}
                    >
                      <Space direction="vertical" size={6} style={{ width: '100%' }}>
                        <Space wrap>
                          <Tag color={status.color}>{status.label}</Tag>
                          {video.sequence ? <Tag>序号 {video.sequence}</Tag> : null}
                          {video.source_label ? <Tag>{video.source_label}</Tag> : null}
                          {onVideoDrop ? <Tag color="blue">可拖拽排序</Tag> : null}
                        </Space>
                        <Text strong>{formatCreativeText(video.asset_name)}</Text>
                        {formatCreativeText(video.asset_excerpt) !== '-' ? (
                          <Text type="secondary">{formatCreativeText(video.asset_excerpt)}</Text>
                        ) : null}
                        {video.duration_seconds ? (
                          <Text type="secondary">时长：{formatCreativeDurationSeconds(video.duration_seconds)}</Text>
                        ) : null}
                        {getVideoWarnings ? getVideoWarnings(video, index) : null}
                        {renderVideoFooter ? renderVideoFooter(video, index) : null}
                      </Space>
                    </div>
                  </List.Item>
                )
              }}
            />
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前还没有入选视频。" />
          )}
        </Card>
      </Space>
    </Card>
  )
}

type CreativeSourceZoneSectionProps = {
  title: string
  subtitle: string
  description: string
  candidates: Array<{
    key: string
    label: string
    items: CreativeZoneMaterialCandidateResponse[]
    emptyDescription: string
    renderItemActions?: (item: CreativeZoneMaterialCandidateResponse, index: number) => ReactNode
  }>
  summary?: ReactNode
  action?: ReactNode
  testId: string
}

function CandidateBucketCard({
  label,
  items,
  emptyDescription,
  renderItemActions,
}: {
  label: string
  items: CreativeZoneMaterialCandidateResponse[]
  emptyDescription: string
  renderItemActions?: (item: CreativeZoneMaterialCandidateResponse, index: number) => ReactNode
}) {
  return (
    <Card size="small" type="inner" title={`${label}（${items.length}）`}>
      {items.length > 0 ? (
        <List
          dataSource={items}
          renderItem={(item, index) => (
            <List.Item
              key={`${item.candidate_type}-${item.asset_id}`}
              actions={renderItemActions ? [renderItemActions(item, index)] : undefined}
            >
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                <Space wrap>
                  {item.is_current_value ? <Tag color="success">当前值</Tag> : null}
                  {item.is_selected ? <Tag color="processing">已入选</Tag> : null}
                  {item.source_product_name ? <Tag>{item.source_product_name}</Tag> : null}
                  {item.source_kind ? <Tag>{item.source_kind}</Tag> : null}
                </Space>
                <Text strong>{formatCreativeText(item.asset_name)}</Text>
                {formatCreativeText(item.asset_excerpt) !== '-' ? (
                  <Text type="secondary">{formatCreativeText(item.asset_excerpt)}</Text>
                ) : null}
                {item.duration_seconds ? (
                  <Text type="secondary">时长：{formatCreativeDurationSeconds(item.duration_seconds)}</Text>
                ) : null}
              </Space>
            </List.Item>
          )}
        />
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyDescription} />
      )}
    </Card>
  )
}

export function CreativeSourceZoneSection({
  title,
  subtitle,
  description,
  candidates,
  summary,
  action,
  testId,
}: CreativeSourceZoneSectionProps) {
  return (
    <Card
      title={title}
      extra={action}
      data-testid={testId}
      style={{ flex: 1, minWidth: 320 }}
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        <Space direction="vertical" size={0}>
          <Text strong>{subtitle}</Text>
          <Text type="secondary">{description}</Text>
        </Space>
        {summary}
        {candidates.map((candidate) => (
          <CandidateBucketCard
            key={candidate.key}
            label={candidate.label}
            items={candidate.items}
            emptyDescription={candidate.emptyDescription}
            renderItemActions={candidate.renderItemActions}
          />
        ))}
      </Space>
    </Card>
  )
}
