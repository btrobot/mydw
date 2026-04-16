import { ArrowRightOutlined } from '@ant-design/icons'
import { PageContainer } from '@ant-design/pro-components'
import { useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Flex,
  List,
  Space,
  Spin,
  Statistic,
  Tag,
  Typography,
} from 'antd'

import CreativeEmptyState from '../components/CreativeEmptyState'
import { useCreatives } from '../hooks/useCreatives'
import {
  creativeStatusMeta,
  formatCreativeTimestamp,
} from '../types/creative'

const { Paragraph, Text, Title } = Typography

export default function CreativeWorkbench() {
  const navigate = useNavigate()
  const { data, isLoading } = useCreatives()

  if (isLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  const items = data?.items ?? []
  const total = data?.total ?? 0

  return (
    <PageContainer
      title="作品工作台"
      subTitle="阶段 A：Creative 骨架与工作台雏形"
      extra={[
        <Button key="tasks" onClick={() => navigate('/task/list')}>
          查看任务列表
        </Button>,
      ]}
    >
      <Space direction="vertical" size={16} style={{ display: 'flex' }}>
        <Card>
          <Statistic title="作品总数" value={total} />
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            当前页面展示 Phase A 的最小作品列表投影；任务页仍保留为执行/诊断视图。
          </Paragraph>
        </Card>

        {items.length === 0 ? (
          <Card>
            <CreativeEmptyState onOpenTaskList={() => navigate('/task/list')} />
          </Card>
        ) : (
          <List
            grid={{ gutter: 16, xs: 1, sm: 1, md: 2, xl: 3 }}
            dataSource={items}
            renderItem={(item) => {
              const statusMeta = creativeStatusMeta[item.status]

              return (
                <List.Item>
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
