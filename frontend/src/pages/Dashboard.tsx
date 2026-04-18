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
      message.success(action === 'start' ? '已启动发布器' : action === 'pause' ? '已暂停发布器' : '已停止发布器')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('操作失败')
      }
    }
  }, [controlPublish])

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
      width: 120,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Alert
        type="info"
        showIcon
        message="运行与发布总览"
        description="这里用于查看系统运行态、发布器状态与关键日志；日常作品处理请进入工作台，AIClip 工作流仍从作品详情进入。"
        action={(
          <Space wrap data-testid="dashboard-primary-cta">
            <Button type="primary" onClick={() => navigate('/creative/workbench')} data-testid="dashboard-open-workbench">进入作品工作台</Button>
            <Button onClick={() => navigate('/task/list')} icon={<UnorderedListOutlined />} data-testid="dashboard-open-task-list">查看任务诊断</Button>
          </Space>
        )}
      />

      <Card title="任务运行概览" size="small" extra={<Text type="secondary">用于观察队列与上传进度，不承担作品主入口职责</Text>}>
        <Row gutter={[12, 12]}>
          <Col span={3}><Statistic title="总任务" value={taskStats.total} /></Col>
          <Col span={3}><Statistic title="草稿" value={taskStats.draft} valueStyle={{ color: '#999' }} /></Col>
          <Col span={3}><Statistic title="合成中" value={taskStats.composing} valueStyle={{ color: '#1677ff' }} /></Col>
          <Col span={3}><Statistic title="待上传" value={taskStats.ready} valueStyle={{ color: '#d46b08' }} /></Col>
          <Col span={3}><Statistic title="上传中" value={taskStats.uploading} valueStyle={{ color: '#1677ff' }} /></Col>
          <Col span={3}><Statistic title="已上传" value={taskStats.uploaded} valueStyle={{ color: '#3f8600' }} /></Col>
          <Col span={3}><Statistic title="失败" value={taskStats.failed} valueStyle={{ color: '#cf1322' }} /></Col>
          <Col span={3}><Statistic title="今日上传" value={taskStats.today_uploaded} valueStyle={{ color: '#3f8600' }} /></Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={8}>
          <Card title="发布器状态" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                用于控制发布器启停，并观察当前运行状态。
              </Paragraph>
              <Space>
                <Tag color={publishStatus.status === 'running' ? 'processing' : 'default'}>
                  {publishStatus.status === 'running' ? '运行中' : publishStatus.status === 'paused' ? '已暂停' : '空闲'}
                </Tag>
              </Space>
              <Space>
                {publishStatus.status === 'running' ? (
                  <Button size="small" icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>暂停</Button>
                ) : (
                  <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>启动</Button>
                )}
              </Space>
            </Space>
          </Card>
        </Col>
        <Col span={8}><Card size="small"><Statistic title="账号" value={sysStats?.total_accounts ?? 0} prefix={<UserOutlined />} suffix={`/ ${sysStats?.active_accounts ?? 0} 活跃`} loading={statsLoading} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="商品" value={sysStats?.total_products ?? 0} prefix={<ShoppingOutlined />} loading={statsLoading} /></Card></Col>
      </Row>

      <Card title="系统日志" extra={<Button size="small" icon={<ReloadOutlined />} onClick={() => refetchLogs()}>刷新</Button>}>
        <Table columns={logColumns} dataSource={logs} rowKey="id" pagination={false} loading={logsLoading} size="small" locale={{ emptyText: logs.length === 0 && !logsLoading ? '暂无日志' : undefined }} />
      </Card>
    </Space>
  )
}
