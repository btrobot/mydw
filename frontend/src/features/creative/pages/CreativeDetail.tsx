import { PageContainer } from '@ant-design/pro-components'
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  Flex,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import CheckDrawer from '../components/CheckDrawer'
import VersionPanel from '../components/VersionPanel'
import { useCreative } from '../hooks/useCreatives'
import {
  creativeReviewConclusionMeta,
  creativeStatusMeta,
  formatCheckConclusion,
  formatCreativeTimestamp,
  getVersionLabel,
} from '../types/creative'

const { Paragraph, Text } = Typography

export default function CreativeDetail() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const creativeId = id ? Number.parseInt(id, 10) : undefined
  const { data: creative, isLoading, isError } = useCreative(creativeId)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const primaryTaskId = useMemo(
    () => creative?.linked_task_ids?.[0],
    [creative?.linked_task_ids],
  )

  const currentVersion = creative?.versions?.find((version) => version.is_current) ?? null

  if (isLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (!creative || isError) {
    return (
      <PageContainer title="作品不存在" onBack={() => navigate('/creative/workbench')}>
        <Empty description="未找到对应作品，或该作品尚未进入当前工作台。" />
      </PageContainer>
    )
  }

  const statusMeta = creativeStatusMeta[creative.status]
  const effectiveCheck = creative.review_summary?.current_check
  const effectiveCheckMeta = effectiveCheck
    ? creativeReviewConclusionMeta[effectiveCheck.conclusion]
    : null

  return (
    <PageContainer
      title={creative.title ?? creative.creative_no}
      subTitle={creative.creative_no}
      onBack={() => navigate('/creative/workbench')}
      extra={[
        primaryTaskId ? (
          <Button key="task-detail" onClick={() => navigate(`/task/${primaryTaskId}`)}>
            查看关联任务
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
          message="Phase B：版本与人工审核闭环"
          description="Task 页面仍然保留为执行诊断视图；当前页面仅承载作品版本与审核结论，不引入发布池、调度切换或 AIClip 工作流迁移。"
        />

        {creative.generation_error_msg ? (
          <Alert
            type="warning"
            showIcon
            message="最近一次合成写回失败"
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
              description="请仅对当前版本执行通过 / 返工 / 驳回操作；历史版本的审核结果会保留，但不会继续作为当前业务结论。"
            />
          )}
        </Card>

        <VersionPanel
          versions={creative.versions ?? []}
          reviewSummary={creative.review_summary}
          onReviewVersion={(version) => {
            if (version.is_current) {
              setDrawerOpen(true)
            }
          }}
        />

        <Card title="关联任务（诊断视图）">
          {(creative.linked_task_ids?.length ?? 0) > 0 ? (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                Task 仍然用于查看执行链路与诊断信息，不作为当前作品业务真相来源。
              </Paragraph>
              <Space wrap>
                {creative.linked_task_ids?.map((taskId) => (
                  <Button
                    key={taskId}
                    onClick={() => navigate(`/task/${taskId}`)}
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
    </PageContainer>
  )
}
