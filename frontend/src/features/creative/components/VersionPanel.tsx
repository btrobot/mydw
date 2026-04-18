import {
  ClockCircleOutlined,
  HistoryOutlined,
  SafetyCertificateOutlined,
  TagOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, List, Space, Tag, Typography } from 'antd'

import type { CreativeReviewSummary, CreativeVersionSummary } from '../types/creative'
import {
  creativeReviewConclusionMeta,
  formatCheckConclusion,
  formatCreativeTimestamp,
  getVersionLabel,
  getVersionTitle,
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
      <Card title="版本与审核记录" data-testid="creative-version-panel">
        <Alert type="info" showIcon message="当前作品还没有版本记录" />
      </Card>
    )
  }

  return (
    <Card
      title="版本与审核记录"
      data-testid="creative-version-panel"
      extra={<Text type="secondary">共 {versions.length} 个版本</Text>}
    >
      <Paragraph type="secondary">
        先确认当前版本与当前有效结论，再回看历史版本与审核轨迹。
      </Paragraph>

      <List
        itemLayout="vertical"
        dataSource={versions}
        renderItem={(version) => {
          const latestCheck = version.latest_check
          const isEffective = isCurrentEffectiveCheck(reviewSummary, latestCheck)
          const currentSummaryCheck = reviewSummary?.current_check

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
                    AIClip 工作流
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
                      当前生效版本
                    </Tag>
                  ) : null}
                  <Tag icon={<HistoryOutlined />}>{version.version_type}</Tag>
                  <Text strong>{getVersionTitle(version)}</Text>
                </Space>

                <Space wrap size={[16, 8]}>
                  <Text type="secondary">
                    <ClockCircleOutlined /> 创建于 {formatCreativeTimestamp(version.created_at)}
                  </Text>
                  <Text type="secondary">Package #{version.package_record_id ?? '-'}</Text>
                  <Text type="secondary">父版本 #{version.parent_version_id ?? '-'}</Text>
                </Space>

                {latestCheck ? (
                  <Card
                    size="small"
                    type="inner"
                    title={(
                      <Space>
                        <SafetyCertificateOutlined />
                        <span>审核记录</span>
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
                            历史结论
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
                          message="当前版本已有新的有效结论"
                          description={`当前有效结论为 ${formatCheckConclusion(currentSummaryCheck)}，此处仅保留历史记录。`}
                        />
                      ) : null}
                    </Space>
                  </Card>
                ) : (
                  <Alert
                    type={version.is_current ? 'info' : 'warning'}
                    showIcon
                    message={version.is_current ? '当前版本还没有有效审核结论' : '该历史版本没有审核记录'}
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
