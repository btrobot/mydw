import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Col,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import {
  PauseCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  ShoppingOutlined,
  UnorderedListOutlined,
  UserOutlined,
} from '@ant-design/icons'

import {
  useControlPublish,
  usePublishStatus,
  useSystemLogs,
  useSystemStats,
  useTaskStats,
} from '../hooks'

const { Paragraph, Text } = Typography

interface TaskStats {
  total: number
  draft: number
  composing: number
  ready: number
  uploading: number
  uploaded: number
  failed: number
  cancelled: number
  today_uploaded: number
}

interface LogItem {
  id: number
  created_at: string
  level: string
  module: string
  message: string
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: statsData, isLoading: statsLoading } = useSystemStats()
  const { data: logsData, isLoading: logsLoading, refetch: refetchLogs } = useSystemLogs()
  const { data: taskStatsRaw } = useTaskStats()
  const {
    data: publishStatus = {
      status: 'idle',
      current_task_id: null,
      total_pending: 0,
      total_success: 0,
      total_failed: 0,
    },
  } = usePublishStatus()
  const controlPublish = useControlPublish()

  const sysStats = statsData as { total_accounts?: number; active_accounts?: number; total_products?: number } | undefined
  const ts = taskStatsRaw as TaskStats | undefined
  const taskStats: TaskStats = {
    total: ts?.total ?? 0,
    draft: ts?.draft ?? 0,
    composing: ts?.composing ?? 0,
    ready: ts?.ready ?? 0,
    uploading: ts?.uploading ?? 0,
    uploaded: ts?.uploaded ?? 0,
    failed: ts?.failed ?? 0,
    cancelled: ts?.cancelled ?? 0,
    today_uploaded: ts?.today_uploaded ?? 0,
  }
  const logs = (logsData as { items: LogItem[] } | undefined)?.items ?? []

  const handlePublish = useCallback(async (action: 'start' | 'pause' | 'stop') => {
    try {
      await controlPublish.mutateAsync({ action })
      message.success(action === 'start' ? 'Publish started' : action === 'pause' ? 'Publish paused' : 'Publish stopped')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('Action failed')
      }
    }
  }, [controlPublish])

  const logColumns = [
    {
      title: 'Time',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const color = level === 'ERROR' ? 'red' : level === 'WARNING' ? 'orange' : 'blue'
        return <Tag color={color}>{level}</Tag>
      },
    },
    {
      title: 'Module',
      dataIndex: 'module',
      key: 'module',
      width: 120,
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Alert
        type="info"
        showIcon
        message="Creative workbench is the main daily workspace"
        description="Use the creative workbench for day-to-day asset review, version checks, and AIClip workflow steps. This dashboard remains a runtime and publish overview, not the primary Task business entry."
        action={(
          <Space wrap data-testid="dashboard-primary-cta">
            <Button
              type="primary"
              onClick={() => navigate('/creative/workbench')}
              data-testid="dashboard-open-workbench"
            >
              Open creative workbench
            </Button>
            <Button
              onClick={() => navigate('/task/list')}
              icon={<UnorderedListOutlined />}
              data-testid="dashboard-open-task-list"
            >
              Open execution / diagnostics tasks
            </Button>
          </Space>
        )}
      />

      <Card title="Execution task overview" size="small" extra={<Text type="secondary">Tasks are secondary execution / diagnostics surfaces</Text>}>
        <Row gutter={[12, 12]}>
          <Col span={3}><Statistic title="Total" value={taskStats.total} /></Col>
          <Col span={3}><Statistic title="Draft" value={taskStats.draft} valueStyle={{ color: '#999' }} /></Col>
          <Col span={3}><Statistic title="Composing" value={taskStats.composing} valueStyle={{ color: '#1677ff' }} /></Col>
          <Col span={3}><Statistic title="Ready" value={taskStats.ready} valueStyle={{ color: '#d46b08' }} /></Col>
          <Col span={3}><Statistic title="Uploading" value={taskStats.uploading} valueStyle={{ color: '#1677ff' }} /></Col>
          <Col span={3}><Statistic title="Uploaded" value={taskStats.uploaded} valueStyle={{ color: '#3f8600' }} /></Col>
          <Col span={3}><Statistic title="Failed" value={taskStats.failed} valueStyle={{ color: '#cf1322' }} /></Col>
          <Col span={3}><Statistic title="Uploaded today" value={taskStats.today_uploaded} valueStyle={{ color: '#3f8600' }} /></Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={8}>
          <Card title="Publish runtime" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                Runtime controls stay on the dashboard, while creative flows continue in the creative workbench.
              </Paragraph>
              <Space>
                <Tag color={publishStatus.status === 'running' ? 'processing' : 'default'}>
                  {publishStatus.status === 'running' ? 'Running' : publishStatus.status === 'paused' ? 'Paused' : 'Idle'}
                </Tag>
              </Space>
              <Space>
                {publishStatus.status === 'running' ? (
                  <Button size="small" icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>
                    Pause
                  </Button>
                ) : (
                  <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>
                    Start
                  </Button>
                )}
              </Space>
            </Space>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="Accounts"
              value={sysStats?.total_accounts ?? 0}
              prefix={<UserOutlined />}
              suffix={`/ ${sysStats?.active_accounts ?? 0} active`}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="Products"
              value={sysStats?.total_products ?? 0}
              prefix={<ShoppingOutlined />}
              loading={statsLoading}
            />
          </Card>
        </Col>
      </Row>

      <Card title="Runtime logs" extra={<Button size="small" icon={<ReloadOutlined />} onClick={() => refetchLogs()}>Refresh</Button>}>
        <Table
          columns={logColumns}
          dataSource={logs}
          rowKey="id"
          pagination={false}
          loading={logsLoading}
          size="small"
          locale={{ emptyText: logs.length === 0 && !logsLoading ? 'No logs yet' : undefined }}
        />
      </Card>
    </Space>
  )
}
