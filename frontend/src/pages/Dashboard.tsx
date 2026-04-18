import {
  PauseCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  ShoppingOutlined,
  UnorderedListOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Col,
  Flex,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'

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
  const systemStatsQuery = useSystemStats()
  const logsQuery = useSystemLogs()
  const taskStatsQuery = useTaskStats()
  const publishStatusQuery = usePublishStatus()
  const controlPublish = useControlPublish()

  const sysStats = systemStatsQuery.data as {
    total_accounts?: number
    active_accounts?: number
    total_products?: number
  } | undefined
  const taskStats = taskStatsQuery.data as TaskStats | undefined
  const publishStatus = publishStatusQuery.data
  const logs = (logsQuery.data as { items: LogItem[] } | undefined)?.items ?? []

  const handlePublish = useCallback(async (action: 'start' | 'pause' | 'stop') => {
    try {
      await controlPublish.mutateAsync({ action })
      message.success(action === 'start' ? '已启动发布器' : action === 'pause' ? '已暂停发布器' : '已停止发布器')
      void publishStatusQuery.refetch()
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('操作失败')
      }
    }
  }, [controlPublish, publishStatusQuery])

  const retryRuntime = useCallback(() => {
    void Promise.all([
      publishStatusQuery.refetch(),
      taskStatsQuery.refetch(),
      systemStatsQuery.refetch(),
      logsQuery.refetch(),
    ])
  }, [logsQuery, publishStatusQuery, systemStatsQuery, taskStatsQuery])

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
      width: 420,
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
        {taskStatsQuery.isLoading && !taskStats ? (
          <Flex justify="center" style={{ padding: 24 }}>
            <Spin />
          </Flex>
        ) : taskStatsQuery.isError ? (
          <Alert
            type="warning"
            showIcon
            message="任务统计暂时不可用"
            description="任务统计请求失败，当前不会再把失败伪装成 0 条任务。"
            action={(
              <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                重试
              </Button>
            )}
            data-testid="dashboard-task-stats-error"
          />
        ) : (
          <Row gutter={[12, 12]}>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="总任务" value={taskStats?.total ?? 0} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="草稿" value={taskStats?.draft ?? 0} valueStyle={{ color: '#999' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="合成中" value={taskStats?.composing ?? 0} valueStyle={{ color: '#1677ff' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="待上传" value={taskStats?.ready ?? 0} valueStyle={{ color: '#d46b08' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="上传中" value={taskStats?.uploading ?? 0} valueStyle={{ color: '#1677ff' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="已上传" value={taskStats?.uploaded ?? 0} valueStyle={{ color: '#3f8600' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="失败" value={taskStats?.failed ?? 0} valueStyle={{ color: '#cf1322' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="今日上传" value={taskStats?.today_uploaded ?? 0} valueStyle={{ color: '#3f8600' }} /></Col>
          </Row>
        )}
      </Card>

      <Row gutter={[16, 16]} align="stretch">
        <Col xs={24} lg={12} xl={8}>
          <Card title="发布器状态" size="small">
            {publishStatusQuery.isLoading && !publishStatus ? (
              <Flex justify="center" style={{ padding: 24 }}>
                <Spin />
              </Flex>
            ) : publishStatusQuery.isError ? (
              <Alert
                type="error"
                showIcon
                message="发布器状态暂时不可用"
                description="发布状态请求失败，当前不会再把失败误显示为空闲。"
                action={(
                  <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                    重试
                  </Button>
                )}
                data-testid="dashboard-publish-status-error"
              />
            ) : (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  用于控制发布器启停，并观察当前运行状态。
                </Paragraph>
                <Space wrap>
                  <Tag color={publishStatus?.status === 'running' ? 'processing' : publishStatus?.status === 'paused' ? 'warning' : 'default'}>
                    {publishStatus?.status === 'running' ? '运行中' : publishStatus?.status === 'paused' ? '已暂停' : '空闲'}
                  </Tag>
                  {publishStatus?.current_task_id ? <Tag>当前任务 #{publishStatus.current_task_id}</Tag> : null}
                </Space>
                <Space wrap>
                  {publishStatus?.status === 'running' ? (
                    <Button size="small" icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>
                      暂停
                    </Button>
                  ) : (
                    <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>
                      启动
                    </Button>
                  )}
                  <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                    刷新状态
                  </Button>
                </Space>
                <Space wrap>
                  <Tag>待处理 {publishStatus?.total_pending ?? 0}</Tag>
                  <Tag color="success">成功 {publishStatus?.total_success ?? 0}</Tag>
                  <Tag color="error">失败 {publishStatus?.total_failed ?? 0}</Tag>
                </Space>
              </Space>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={8}>
          <Card size="small">
            <Statistic
              title="账号"
              value={systemStatsQuery.isError ? '--' : sysStats?.total_accounts ?? 0}
              prefix={<UserOutlined />}
              suffix={systemStatsQuery.isError ? '' : `/ ${sysStats?.active_accounts ?? 0} 活跃`}
              loading={systemStatsQuery.isLoading && !systemStatsQuery.isError}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={8}>
          <Card size="small">
            <Statistic
              title="商品"
              value={systemStatsQuery.isError ? '--' : sysStats?.total_products ?? 0}
              prefix={<ShoppingOutlined />}
              loading={systemStatsQuery.isLoading && !systemStatsQuery.isError}
            />
          </Card>
        </Col>
      </Row>

      {systemStatsQuery.isError ? (
        <Alert
          type="warning"
          showIcon
          message="系统统计暂时不可用"
          description="账号 / 商品统计请求失败，因此当前显示为不可用，而不是回落成 0。"
          action={(
            <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
              重试
            </Button>
          )}
          data-testid="dashboard-system-stats-error"
        />
      ) : null}

      <Card title="系统日志" extra={<Button size="small" icon={<ReloadOutlined />} onClick={() => logsQuery.refetch()}>刷新</Button>}>
        {logsQuery.isError ? (
          <Alert
            type="warning"
            showIcon
            message="系统日志暂时不可用"
            description="日志请求失败，当前不会把失败误显示成“暂无日志”。"
            action={(
              <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                重试
              </Button>
            )}
            data-testid="dashboard-logs-error"
          />
        ) : (
          <Table
            columns={logColumns}
            dataSource={logs}
            rowKey="id"
            pagination={false}
            loading={logsQuery.isLoading}
            size="small"
            scroll={{ x: 760 }}
            locale={{ emptyText: logs.length === 0 && !logsQuery.isLoading ? '暂无日志' : undefined }}
          />
        )}
      </Card>
    </Space>
  )
}
