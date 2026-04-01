import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Space } from 'antd'
import {
  UserOutlined,
  VideoCameraOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { api } from '../services/api'

interface Stats {
  total_accounts: number
  active_accounts: number
  total_tasks: number
  pending_tasks: number
  success_tasks: number
  failed_tasks: number
  total_products: number
  total_materials: number
}

interface Log {
  id: number
  level: string
  module: string
  message: string
  created_at: string
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    total_accounts: 0,
    active_accounts: 0,
    total_tasks: 0,
    pending_tasks: 0,
    success_tasks: 0,
    failed_tasks: 0,
    total_products: 0,
    total_materials: 0,
  })
  const [logs, setLogs] = useState<Log[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    // 定时刷新
    const timer = setInterval(fetchData, 30000)
    return () => clearInterval(timer)
  }, [])

  const fetchData = async () => {
    try {
      const [statsRes, logsRes] = await Promise.all([
        api.get('/system/stats'),
        api.get('/system/logs?limit=10'),
      ])
      setStats(statsRes.data)
      setLogs(logsRes.data.items || [])
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
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
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="账号总数"
              value={stats.total_accounts}
              prefix={<UserOutlined />}
              suffix={`/ ${stats.active_accounts} 活跃`}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待发布任务"
              value={stats.pending_tasks}
              prefix={<ClockCircleOutlined />}
              suffix={`/ ${stats.total_tasks} 总计`}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="发布成功"
              value={stats.success_tasks}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="发布失败"
              value={stats.failed_tasks}
              prefix={<VideoCameraOutlined />}
              valueStyle={{ color: '#cf1322' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Card title="运行日志" extra={<a onClick={fetchData}>刷新</a>}>
        <Table
          columns={logColumns}
          dataSource={logs}
          rowKey="id"
          pagination={false}
          loading={loading}
          size="small"
        />
      </Card>
    </Space>
  )
}
