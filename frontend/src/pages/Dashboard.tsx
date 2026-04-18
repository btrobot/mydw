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
      message.success(action === 'start' ? '\u5df2\u542f\u52a8\u53d1\u5e03\u5668' : action === 'pause' ? '\u5df2\u6682\u505c\u53d1\u5e03\u5668' : '\u5df2\u505c\u6b62\u53d1\u5e03\u5668')
      void publishStatusQuery.refetch()
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('\u64cd\u4f5c\u5931\u8d25')
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
      title: '\u65f6\u95f4',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '\u7ea7\u522b',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const color = level === 'ERROR' ? 'red' : level === 'WARNING' ? 'orange' : 'blue'
        return <Tag color={color}>{level}</Tag>
      },
    },
    {
      title: '\u6a21\u5757',
      dataIndex: 'module',
      key: 'module',
      width: 120,
    },
    {
      title: '\u6d88\u606f',
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
        message="\u8fd0\u884c\u4e0e\u53d1\u5e03\u603b\u89c8"
        description="\u8fd9\u91cc\u7528\u4e8e\u67e5\u770b\u7cfb\u7edf\u8fd0\u884c\u6001\u3001\u53d1\u5e03\u5668\u72b6\u6001\u4e0e\u5173\u952e\u65e5\u5fd7\uff1b\u65e5\u5e38\u4f5c\u54c1\u5904\u7406\u8bf7\u8fdb\u5165\u5de5\u4f5c\u53f0\uff0cAIClip \u5de5\u4f5c\u6d41\u4ecd\u4ece\u4f5c\u54c1\u8be6\u60c5\u8fdb\u5165\u3002"
        action={(
          <Space wrap data-testid="dashboard-primary-cta">
            <Button type="primary" onClick={() => navigate('/creative/workbench')} data-testid="dashboard-open-workbench">\u8fdb\u5165\u4f5c\u54c1\u5de5\u4f5c\u53f0</Button>
            <Button onClick={() => navigate('/task/list')} icon={<UnorderedListOutlined />} data-testid="dashboard-open-task-list">\u67e5\u770b\u4efb\u52a1\u8bca\u65ad</Button>
          </Space>
        )}
      />

      <Card title="\u4efb\u52a1\u8fd0\u884c\u6982\u89c8" size="small" extra={<Text type="secondary">\u7528\u4e8e\u89c2\u5bdf\u961f\u5217\u4e0e\u4e0a\u4f20\u8fdb\u5ea6\uff0c\u4e0d\u627f\u62c5\u4f5c\u54c1\u4e3b\u5165\u53e3\u804c\u8d23</Text>}>
        {taskStatsQuery.isLoading && !taskStats ? (
          <Flex justify="center" style={{ padding: 24 }}>
            <Spin />
          </Flex>
        ) : taskStatsQuery.isError ? (
          <Alert
            type="warning"
            showIcon
            message="\u4efb\u52a1\u7edf\u8ba1\u6682\u65f6\u4e0d\u53ef\u7528"
            description="\u4efb\u52a1\u7edf\u8ba1\u8bf7\u6c42\u5931\u8d25\uff0c\u5f53\u524d\u4e0d\u4f1a\u518d\u628a\u5931\u8d25\u4f2a\u88c5\u6210 0 \u6761\u4efb\u52a1\u3002"
            action={(
              <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                \u91cd\u8bd5
              </Button>
            )}
            data-testid="dashboard-task-stats-error"
          />
        ) : (
          <Row gutter={[12, 12]}>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u603b\u4efb\u52a1" value={taskStats?.total ?? 0} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u8349\u7a3f" value={taskStats?.draft ?? 0} valueStyle={{ color: '#999' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u5408\u6210\u4e2d" value={taskStats?.composing ?? 0} valueStyle={{ color: '#1677ff' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u5f85\u4e0a\u4f20" value={taskStats?.ready ?? 0} valueStyle={{ color: '#d46b08' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u4e0a\u4f20\u4e2d" value={taskStats?.uploading ?? 0} valueStyle={{ color: '#1677ff' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u5df2\u4e0a\u4f20" value={taskStats?.uploaded ?? 0} valueStyle={{ color: '#3f8600' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u5931\u8d25" value={taskStats?.failed ?? 0} valueStyle={{ color: '#cf1322' }} /></Col>
            <Col xs={12} sm={8} md={6} xl={3}><Statistic title="\u4eca\u65e5\u4e0a\u4f20" value={taskStats?.today_uploaded ?? 0} valueStyle={{ color: '#3f8600' }} /></Col>
          </Row>
        )}
      </Card>

      <Row gutter={[16, 16]} align="stretch">
        <Col xs={24} lg={12} xl={8}>
          <Card title="\u53d1\u5e03\u5668\u72b6\u6001" size="small">
            {publishStatusQuery.isLoading && !publishStatus ? (
              <Flex justify="center" style={{ padding: 24 }}>
                <Spin />
              </Flex>
            ) : publishStatusQuery.isError ? (
              <Alert
                type="error"
                showIcon
                message="\u53d1\u5e03\u5668\u72b6\u6001\u6682\u65f6\u4e0d\u53ef\u7528"
                description="\u53d1\u5e03\u72b6\u6001\u8bf7\u6c42\u5931\u8d25\uff0c\u5f53\u524d\u4e0d\u4f1a\u518d\u628a\u5931\u8d25\u8bef\u663e\u793a\u4e3a\u7a7a\u95f2\u3002"
                action={(
                  <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                    \u91cd\u8bd5
                  </Button>
                )}
                data-testid="dashboard-publish-status-error"
              />
            ) : (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  \u7528\u4e8e\u63a7\u5236\u53d1\u5e03\u5668\u542f\u505c\uff0c\u5e76\u89c2\u5bdf\u5f53\u524d\u8fd0\u884c\u72b6\u6001\u3002
                </Paragraph>
                <Space wrap>
                  <Tag color={publishStatus?.status === 'running' ? 'processing' : publishStatus?.status === 'paused' ? 'warning' : 'default'}>
                    {publishStatus?.status === 'running' ? '\u8fd0\u884c\u4e2d' : publishStatus?.status === 'paused' ? '\u5df2\u6682\u505c' : '\u7a7a\u95f2'}
                  </Tag>
                  {publishStatus?.current_task_id ? <Tag>\u5f53\u524d\u4efb\u52a1 #{publishStatus.current_task_id}</Tag> : null}
                </Space>
                <Space wrap>
                  {publishStatus?.status === 'running' ? (
                    <Button size="small" icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>
                      \u6682\u505c
                    </Button>
                  ) : (
                    <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>
                      \u542f\u52a8
                    </Button>
                  )}
                  <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                    \u5237\u65b0\u72b6\u6001
                  </Button>
                </Space>
                <Space wrap>
                  <Tag>\u5f85\u5904\u7406 {publishStatus?.total_pending ?? 0}</Tag>
                  <Tag color="success">\u6210\u529f {publishStatus?.total_success ?? 0}</Tag>
                  <Tag color="error">\u5931\u8d25 {publishStatus?.total_failed ?? 0}</Tag>
                </Space>
              </Space>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={8}>
          <Card size="small">
            <Statistic
              title="\u8d26\u53f7"
              value={systemStatsQuery.isError ? '--' : sysStats?.total_accounts ?? 0}
              prefix={<UserOutlined />}
              suffix={systemStatsQuery.isError ? '' : `/ ${sysStats?.active_accounts ?? 0} \u6d3b\u8dc3`}
              loading={systemStatsQuery.isLoading && !systemStatsQuery.isError}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={8}>
          <Card size="small">
            <Statistic
              title="\u5546\u54c1"
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
          message="\u7cfb\u7edf\u7edf\u8ba1\u6682\u65f6\u4e0d\u53ef\u7528"
          description="\u8d26\u53f7 / \u5546\u54c1\u7edf\u8ba1\u8bf7\u6c42\u5931\u8d25\uff0c\u56e0\u6b64\u5f53\u524d\u663e\u793a\u4e3a\u4e0d\u53ef\u7528\uff0c\u800c\u4e0d\u662f\u56de\u843d\u6210 0\u3002"
          action={(
            <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
              \u91cd\u8bd5
            </Button>
          )}
          data-testid="dashboard-system-stats-error"
        />
      ) : null}

      <Card title="\u7cfb\u7edf\u65e5\u5fd7" extra={<Button size="small" icon={<ReloadOutlined />} onClick={() => logsQuery.refetch()}>\u5237\u65b0</Button>}>
        {logsQuery.isError ? (
          <Alert
            type="warning"
            showIcon
            message="\u7cfb\u7edf\u65e5\u5fd7\u6682\u65f6\u4e0d\u53ef\u7528"
            description="\u65e5\u5fd7\u8bf7\u6c42\u5931\u8d25\uff0c\u5f53\u524d\u4e0d\u4f1a\u628a\u5931\u8d25\u8bef\u663e\u793a\u6210\u201c\u6682\u65e0\u65e5\u5fd7\u201d\u3002"
            action={(
              <Button size="small" icon={<ReloadOutlined />} onClick={retryRuntime}>
                \u91cd\u8bd5
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
            locale={{ emptyText: logs.length === 0 && !logsQuery.isLoading ? '\u6682\u65e0\u65e5\u5fd7' : undefined }}
          />
        )}
      </Card>
    </Space>
  )
}
