import {
  ClockCircleOutlined,
  HistoryOutlined,
  SafetyCertificateOutlined,
  TagOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, Descriptions, List, Space, Tag, Typography } from 'antd'

import type { CreativeReviewSummary, CreativeVersionSummary } from '../types/creative'
import {
  creativeReviewConclusionMeta,
  formatCheckConclusion,
  formatCreativeDurationSeconds,
  formatCreativeText,
  formatCreativeTimestamp,
  getVersionLabel,
  getVersionTitle,
  hasPackageFrozenTruth,
  hasVersionAdoptedTruth,
  isCurrentEffectiveCheck,
} from '../types/creative'

const { Paragraph, Text } = Typography

interface VersionPanelProps {
  versions: CreativeVersionSummary[]
  reviewSummary?: CreativeReviewSummary | null
  onReviewVersion?: (version: CreativeVersionSummary) => void
  onOpenAiClipWorkflow?: (version: CreativeVersionSummary) => void
}

export default function VersionPanel({
  versions,
  reviewSummary,
  onReviewVersion,
  onOpenAiClipWorkflow,
}: VersionPanelProps) {
  if (versions.length === 0) {
    return (
      <Card title="版本结果与审核记录" data-testid="creative-version-panel">
        <Alert type="info" showIcon message="当前作品还没有版本结果记录" />
      </Card>
    )
  }

  return (
    <Card
      title="版本结果与审核记录"
      data-testid="creative-version-panel"
      extra={<Text type="secondary">共 {versions.length} 个版本</Text>}
    >
      <Paragraph type="secondary" data-testid="creative-version-semantics">
        这里按“作品定义 → 版本结果 → 审核结论”查看历史；Package 仅表示发布侧承接记录，不替代作品定义。
      </Paragraph>

      <List
        itemLayout="vertical"
        dataSource={versions}
        renderItem={(version) => {
          const latestCheck = version.latest_check
          const isEffective = isCurrentEffectiveCheck(reviewSummary, latestCheck)
          const currentSummaryCheck = reviewSummary?.current_check
          const packageRecord = version.package_record

          return (
            <List.Item
              key={version.id}
              data-testid={`creative-version-item-${version.id}`}
              actions={[
                version.is_current && onOpenAiClipWorkflow ? (
                  <Button
                    key="ai-clip"
                    size="small"
                    onClick={() => onOpenAiClipWorkflow(version)}
                    data-testid={`creative-version-ai-clip-${version.id}`}
                  >
                    进入 AIClip
                  </Button>
                ) : null,
                version.is_current && onReviewVersion ? (
                  <Button
                    key="review"
                    type="primary"
                    size="small"
                    onClick={() => onReviewVersion(version)}
                  >
                    审核当前版本
                  </Button>
                ) : null,
              ].filter(Boolean)}
            >
              <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <Space wrap>
                  <Tag color={version.is_current ? 'blue' : 'default'} icon={<TagOutlined />}>
                    {getVersionLabel(version.version_no)}
                  </Tag>
                  {version.is_current ? (
                    <Tag color="processing" data-testid={`creative-version-current-${version.id}`}>
                      当前生效版本结果
                    </Tag>
                  ) : null}
                  <Tag icon={<HistoryOutlined />}>{version.version_type}</Tag>
                  <Text strong>{getVersionTitle(version)}</Text>
                </Space>

                <Space wrap size={[16, 8]}>
                  <Text type="secondary">
                    <ClockCircleOutlined /> 创建于 {formatCreativeTimestamp(version.created_at)}
                  </Text>
                  <Text type="secondary">发布侧 PackageRecord #{version.package_record_id ?? '-'}</Text>
                  <Text type="secondary">父版本 #{version.parent_version_id ?? '-'}</Text>
                </Space>

                <Card
                  size="small"
                  type="inner"
                  title="版本采用值"
                  data-testid={`creative-version-adopted-${version.id}`}
                >
                  {hasVersionAdoptedTruth(version) ? (
                    <Descriptions size="small" column={1}>
                      <Descriptions.Item label="结果时长">
                        {formatCreativeDurationSeconds(version.actual_duration_seconds)}
                      </Descriptions.Item>
                      <Descriptions.Item label="成片路径">
                        {formatCreativeText(version.final_video_path)}
                      </Descriptions.Item>
                      <Descriptions.Item label="最终商品名">
                        {formatCreativeText(version.final_product_name)}
                      </Descriptions.Item>
                      <Descriptions.Item label="最终文案">
                        {formatCreativeText(version.final_copywriting_text)}
                      </Descriptions.Item>
                    </Descriptions>
                  ) : (
                    <Alert
                      type="info"
                      showIcon
                      message="该版本尚未沉淀可展示的采用值"
                    />
                  )}
                </Card>

                <Card
                  size="small"
                  type="inner"
                  title="发布包冻结值"
                  data-testid={`creative-version-package-freeze-${version.id}`}
                >
                  {packageRecord ? (
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      <Text type="secondary">PackageRecord #{packageRecord.id}</Text>
                      {hasPackageFrozenTruth(packageRecord) ? (
                        <Descriptions size="small" column={1}>
                          <Descriptions.Item label="冻结视频">
                            {formatCreativeText(packageRecord.frozen_video_path)}
                          </Descriptions.Item>
                          <Descriptions.Item label="冻结封面">
                            {formatCreativeText(packageRecord.frozen_cover_path)}
                          </Descriptions.Item>
                          <Descriptions.Item label="冻结时长">
                            {formatCreativeDurationSeconds(packageRecord.frozen_duration_seconds)}
                          </Descriptions.Item>
                          <Descriptions.Item label="冻结商品名">
                            {formatCreativeText(packageRecord.frozen_product_name)}
                          </Descriptions.Item>
                          <Descriptions.Item label="冻结文案">
                            {formatCreativeText(packageRecord.frozen_copywriting_text)}
                          </Descriptions.Item>
                        </Descriptions>
                      ) : (
                        <Alert
                          type="info"
                          showIcon
                          message="该发布包已建立关联，但冻结四件套尚未返回"
                        />
                      )}
                    </Space>
                  ) : (
                    <Alert
                      type="info"
                      showIcon
                      message="当前版本尚未生成发布包冻结值"
                    />
                  )}
                </Card>

                {latestCheck ? (
                  <Card
                    size="small"
                    type="inner"
                    title={(
                      <Space>
                        <SafetyCertificateOutlined />
                        <span>版本审核记录</span>
                      </Space>
                    )}
                    data-testid={`creative-version-check-${version.id}`}
                  >
                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                      <Space wrap>
                        <Tag color={creativeReviewConclusionMeta[latestCheck.conclusion].color}>
                          {formatCheckConclusion(latestCheck)}
                        </Tag>
                        {isEffective ? (
                          <Tag color="success" data-testid="creative-effective-check">
                            当前有效结论
                          </Tag>
                        ) : (
                          <Tag color="default" data-testid={`creative-stale-check-${version.id}`}>
                            历史审核结论
                          </Tag>
                        )}
                      </Space>
                      <Text type="secondary">
                        更新于 {formatCreativeTimestamp(latestCheck.updated_at)}
                      </Text>
                      {latestCheck.note ? (
                        <Paragraph style={{ marginBottom: 0 }}>{latestCheck.note}</Paragraph>
                      ) : null}
                      {!isEffective && version.is_current && currentSummaryCheck ? (
                        <Alert
                          type="warning"
                          showIcon
                          message="当前版本结果已有新的有效结论"
                          description={`当前有效结论为 ${formatCheckConclusion(currentSummaryCheck)}，此处仅保留历史记录。`}
                        />
                      ) : null}
                    </Space>
                  </Card>
                ) : (
                  <Alert
                    type={version.is_current ? 'info' : 'warning'}
                    showIcon
                    message={version.is_current ? '当前版本结果待审核' : '该历史版本没有审核记录'}
                  />
                )}
              </Space>
            </List.Item>
          )
        }}
      />
    </Card>
  )
}
