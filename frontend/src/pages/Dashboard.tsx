import { Card, Row, Col, Statistic, Table, Tag, Space } from 'antd'
import {
  UserOutlined,
  VideoCameraOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useSystemStats, useSystemLogs } from '../hooks'

interface SystemStats {
  total_accounts: number
  active_accounts: number
  total_tasks: number
  pending_tasks: number
  success_tasks: number
  failed_tasks: number
  total_products: number
  total_materials: number
}

interface LogItem {
  id: number
  created_at: string
  level: string
  module: string
  message: string
}

export default function Dashboard() {
  // 使用 React Query hooks
  const { data: statsData, isLoading: statsLoading, refetch: refetchStats } = useSystemStats()
  const { data: logsData, isLoading: logsLoading, refetch: refetchLogs } = useSystemLogs()

  // 规范化数据
  const stats: SystemStats = (statsData as SystemStats) || {
    total_accounts: 0,
    active_accounts: 0,
    total_tasks: 0,
    pending_tasks: 0,
    success_tasks: 0,
    failed_tasks: 0,
    total_products: 0,
    total_materials: 0,
  }
  const logs = (logsData as { items: LogItem[] })?.items || []

  // 统一刷新函数
  const refreshData = () => {
    refetchStats()
    refetchLogs()
  }

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const color = level === 'ERROR' ? 'red' : level === 'WARNING' ? 'orange' : 'blue'
        return <Tag color={color}>{level}</Tag>
      },
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 100,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
  ]

  return (
    <>
      {/* <Title level={1} style={{ marginBottom: 24 }}>数据看板</Title> */}
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="账号总数"
                value={stats.total_accounts}
                prefix={<UserOutlined />}
                suffix={`/ ${stats.active_accounts} 活跃`}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="待发布任务"
                value={stats.pending_tasks}
                prefix={<ClockCircleOutlined />}
                suffix={`/ ${stats.total_tasks} 总计`}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="发布成功"
                value={stats.success_tasks}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#3f8600' }}
                loading={statsLoading}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="发布失败"
                value={stats.failed_tasks}
                prefix={<VideoCameraOutlined />}
                valueStyle={{ color: '#cf1322' }}
                loading={statsLoading}
              />
            </Card>
          </Col>
        </Row>

        <Card title="运行日志" extra={<a onClick={refreshData}>刷新</a>}>
          <Table
            columns={logColumns}
            dataSource={logs}
            rowKey="id"
            pagination={false}
            loading={logsLoading}
            size="small"
            locale={{
              emptyText: logs.length === 0 && !logsLoading
                ? '暂无日志记录'
                : undefined
            }}
          />
        </Card>
      </Space>
    </>
  )
}
