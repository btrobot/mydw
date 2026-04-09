import { useCallback } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Space, Button, message } from 'antd'
import {
  UserOutlined,

  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  ShoppingOutlined,
} from '@ant-design/icons'
import {
  useSystemStats,
  useSystemLogs,
  useTaskStats,
  usePublishStatus,
  useControlPublish,
} from '../hooks'

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
  const { data: statsData, isLoading: statsLoading } = useSystemStats()
  const { data: logsData, isLoading: logsLoading, refetch: refetchLogs } = useSystemLogs()
  const { data: taskStatsRaw } = useTaskStats()
  const { data: publishStatus = { status: 'idle', current_task_id: null, total_pending: 0, total_success: 0, total_failed: 0 } } = usePublishStatus()
  const controlPublish = useControlPublish()

  const sysStats = statsData as { total_accounts?: number; active_accounts?: number; total_products?: number } | undefined
  const ts = taskStatsRaw as unknown as TaskStats | undefined
  const taskStats: TaskStats = {
    total:         ts?.total         ?? 0,
    draft:         ts?.draft         ?? 0,
    composing:     ts?.composing     ?? 0,
    ready:         ts?.ready         ?? 0,
    uploading:     ts?.uploading     ?? 0,
    uploaded:      ts?.uploaded      ?? 0,
    failed:        ts?.failed        ?? 0,
    cancelled:     ts?.cancelled     ?? 0,
    today_uploaded: ts?.today_uploaded ?? 0,
  }
  const logs = (logsData as { items: LogItem[] })?.items || []

  const handlePublish = useCallback(async (action: 'start' | 'pause' | 'stop') => {
    try {
      await controlPublish.mutateAsync({ action })
      message.success(action === 'start' ? '开始发布' : action === 'pause' ? '暂停发布' : '停止发布')
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
      {/* 任务统计 */}
      <Card title="任务概览" size="small">
        <Row gutter={[12, 12]}>
          <Col span={3}><Statistic title="总计" value={taskStats.total} /></Col>
          <Col span={3}><Statistic title="草稿" value={taskStats.draft} valueStyle={{ color: '#999' }} /></Col>
          <Col span={3}><Statistic title="合成中" value={taskStats.composing} valueStyle={{ color: '#1677ff' }} /></Col>
          <Col span={3}><Statistic title="待上传" value={taskStats.ready} valueStyle={{ color: '#d46b08' }} /></Col>
          <Col span={3}><Statistic title="上传中" value={taskStats.uploading} valueStyle={{ color: '#1677ff' }} /></Col>
          <Col span={3}><Statistic title="已上传" value={taskStats.uploaded} valueStyle={{ color: '#3f8600' }} /></Col>
          <Col span={3}><Statistic title="失败" value={taskStats.failed} valueStyle={{ color: '#cf1322' }} /></Col>
          <Col span={3}><Statistic title="今日上传" value={taskStats.today_uploaded} valueStyle={{ color: '#3f8600' }} /></Col>
        </Row>
      </Card>

      {/* 发布控制 + 系统概览 */}
      <Row gutter={16}>
        <Col span={8}>
          <Card title="发布控制" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Tag color={publishStatus.status === 'running' ? 'processing' : 'default'}>
                  {publishStatus.status === 'running' ? '运行中' : publishStatus.status === 'paused' ? '已暂停' : '空闲'}
                </Tag>
              </Space>
              <Space>
                {publishStatus.status === 'running' ? (
                  <Button size="small" icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>
                    暂停
                  </Button>
                ) : (
                  <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>
                    开始
                  </Button>
                )}
              </Space>
            </Space>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="账号总数"
              value={sysStats?.total_accounts ?? 0}
              prefix={<UserOutlined />}
              suffix={`/ ${sysStats?.active_accounts ?? 0} 活跃`}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="商品总数"
              value={sysStats?.total_products ?? 0}
              prefix={<ShoppingOutlined />}
              loading={statsLoading}
            />
          </Card>
        </Col>
      </Row>

      {/* 运行日志 */}
      <Card title="运行日志" extra={<Button size="small" icon={<ReloadOutlined />} onClick={() => refetchLogs()}>刷新</Button>}>
        <Table
          columns={logColumns}
          dataSource={logs}
          rowKey="id"
          pagination={false}
          loading={logsLoading}
          size="small"
          locale={{ emptyText: logs.length === 0 && !logsLoading ? '暂无日志记录' : undefined }}
        />
      </Card>
    </Space>
  )
}
