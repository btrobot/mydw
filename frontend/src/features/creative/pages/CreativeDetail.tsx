import { PageContainer } from '@ant-design/pro-components'
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  Flex,
  List,
  Space,
  Spin,
  Tag,
  Typography,
} from 'antd'
import { useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { useCreative } from '../hooks/useCreatives'
import {
  creativeStatusMeta,
  formatCreativeTimestamp,
} from '../types/creative'

const { Paragraph, Text } = Typography

export default function CreativeDetail() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const creativeId = id ? Number.parseInt(id, 10) : undefined
  const { data: creative, isLoading, isError } = useCreative(creativeId)

  const primaryTaskId = useMemo(
    () => creative?.linked_task_ids?.[0],
    [creative?.linked_task_ids],
  )

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
        <Empty description="未找到对应作品，或该作品尚未进入阶段 A 工作台。" />
      </PageContainer>
    )
  }

  const statusMeta = creativeStatusMeta[creative.status]

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
        <Button key="task-list" onClick={() => navigate('/task/list')}>
          返回任务列表
        </Button>,
      ].filter(Boolean)}
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Alert
          type="info"
          showIcon
          message="Phase A 仅提供作品骨架视图"
          description="任务页仍保留为执行/诊断主视图；版本管理、人工检查、发布池和 AIClip workflow 尚未在这里接入。"
        />

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
                V{creative.current_version.version_no}
              </Descriptions.Item>
              <Descriptions.Item label="版本标题" span={2}>
                {creative.current_version.title ?? '未命名版本'}
              </Descriptions.Item>
              <Descriptions.Item label="PackageRecord ID" span={2}>
                {creative.current_version.package_record_id ?? '-'}
              </Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description="当前作品还没有版本投影。" />
          )}
        </Card>

        <Card title="关联任务">
          {(creative.linked_task_ids?.length ?? 0) > 0 ? (
            <List
              dataSource={creative.linked_task_ids ?? []}
              renderItem={(taskId) => (
                <List.Item
                  actions={[
                    <Button
                      key={`task-${taskId}`}
                      type="link"
                      onClick={() => navigate(`/task/${taskId}`)}
                    >
                      打开任务详情
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={`任务 #${taskId}`}
                    description="阶段 A 仅提供最小诊断投影；更完整的执行信息仍在任务详情页。"
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty description="当前作品还没有关联任务。" />
          )}
        </Card>

        <Card title="阶段说明">
          <Paragraph style={{ marginBottom: 0 }}>
            当前详情页只展示阶段 A 的最小作品、版本与任务映射信息，为后续版本管理与人工检查闭环打底。
          </Paragraph>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            <Text strong>未纳入本阶段：</Text>
            审核通过 / 返工 / 拒绝、发布池、调度切换、AIClip workflow。
          </Paragraph>
        </Card>
      </Space>
    </PageContainer>
  )
}
