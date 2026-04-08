import { useParams, useNavigate } from 'react-router-dom'
import { Button, Space, Tag, Spin, Empty } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { PageContainer, ProDescriptions, ProTable } from '@ant-design/pro-components'
import type { ProColumns } from '@ant-design/pro-components'

import { useTopicGroups } from '@/hooks'
import type { TopicResponse } from '@/types/material'

export default function TopicGroupDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: topicGroups = [], isFetching } = useTopicGroups()
  const group = topicGroups.find((g) => g.id === Number(id))

  if (isFetching) {
    return (
      <PageContainer>
        <div style={{ textAlign: 'center', padding: '48px 0' }}>
          <Spin size="large" />
        </div>
      </PageContainer>
    )
  }

  if (!group) {
    return (
      <PageContainer>
        <Empty description="话题组不存在" />
      </PageContainer>
    )
  }

  const topicColumns: ProColumns<TopicResponse>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 70,
    },
    {
      title: '话题名称',
      dataIndex: 'name',
      ellipsis: true,
    },
    {
      title: '热度',
      dataIndex: 'heat',
      width: 100,
      render: (_, record) => record.heat.toLocaleString(),
    },
    {
      title: '来源',
      dataIndex: 'source',
      width: 80,
      render: (_, record) => (
        <Tag color={record.source === 'manual' ? 'default' : 'blue'}>
          {record.source === 'manual' ? '手动' : '搜索'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      render: (_, record) => new Date(record.created_at).toLocaleString('zh-CN'),
    },
  ]

  return (
    <PageContainer
      title={group.name}
      extra={
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/material/topic-group')}>
          返回列表
        </Button>
      }
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <ProDescriptions
          column={2}
          dataSource={group}
          columns={[
            {
              title: 'ID',
              dataIndex: 'id',
            },
            {
              title: '名称',
              dataIndex: 'name',
            },
            {
              title: '话题数量',
              render: () => group.topic_ids.length,
            },
            {
              title: '创建时间',
              dataIndex: 'created_at',
              render: (_, record) => new Date(record.created_at).toLocaleString('zh-CN'),
            },
            {
              title: '更新时间',
              dataIndex: 'updated_at',
              render: (_, record) => new Date(record.updated_at).toLocaleString('zh-CN'),
            },
          ]}
        />

        <ProTable<TopicResponse>
          rowKey="id"
          columns={topicColumns}
          dataSource={group.topics}
          search={false}
          toolBarRender={false}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
          size="small"
          headerTitle="关联话题"
        />
      </Space>
    </PageContainer>
  )
}
