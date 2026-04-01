import { useEffect, useState } from 'react'
import {
  Table, Tag, Button, Space, Modal, Form, Input, Select,
  message, Popconfirm, Row, Col, Card, Statistic
} from 'antd'
import {
  PlusOutlined, PlayCircleOutlined, PauseCircleOutlined,
  ReloadOutlined, SwapOutlined, ThunderboltOutlined,
  SyncOutlined
} from '@ant-design/icons'
import { api } from '../services/api'

interface Task {
  id: number
  account_id: number
  product_id: number | null
  video_path: string | null
  content: string | null
  topic: string | null
  cover_path: string | null
  status: string
  publish_time: string | null
  error_msg: string | null
  priority: number
  created_at: string
}

interface Account {
  id: number
  account_name: string
  status: string
}

interface TaskStats {
  total: number
  pending: number
  running: number
  success: number
  failed: number
  paused: number
  today_success: number
}

interface PublishStatus {
  status: string
  current_task_id: number | null
  total_pending: number
  total_success: number
  total_failed: number
}

export default function Task() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [publishStatus, setPublishStatus] = useState<PublishStatus>({
    status: 'idle',
    current_task_id: null,
    total_pending: 0,
    total_success: 0,
    total_failed: 0
  })
  const [stats, setStats] = useState<TaskStats>({
    total: 0, pending: 0, running: 0, success: 0, failed: 0, paused: 0, today_success: 0
  })
  const [form] = Form.useForm()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [tasksRes, accountsRes, publishRes, statsRes] = await Promise.all([
        api.get('/tasks?limit=100'),
        api.get('/accounts'),
        api.get('/publish/status'),
        api.get('/tasks/stats')
      ])
      setTasks(tasksRes.data.items || [])
      setAccounts(accountsRes.data || [])
      setPublishStatus(publishRes.data)
      setStats(statsRes.data)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    form.resetFields()
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      await api.post('/tasks', values)
      message.success('添加任务成功')
      setModalVisible(false)
      fetchData()
    } catch (error: any) {
      if (error.errorFields) return
      message.error(error.response?.data?.detail || '添加失败')
    }
  }

  const handlePublish = async (action: 'start' | 'pause' | 'stop') => {
    try {
      await api.post('/publish/control', { action })
      message.success(action === 'start' ? '开始发布' : action === 'pause' ? '暂停发布' : '停止发布')
      fetchData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleShuffle = async () => {
    try {
      await api.post('/tasks/shuffle')
      message.success('任务顺序已打乱')
      fetchData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleAutoGenerate = async () => {
    if (accounts.length === 0) {
      message.warning('请先添加账号')
      return
    }

    Modal.confirm({
      title: '自动生成任务',
      content: (
        <Form form={form} layout="vertical">
          <Form.Item
            name="account_id"
            label="选择账号"
            rules={[{ required: true, message: '请选择账号' }]}
            initialValue={accounts[0]?.id}
          >
            <Select>
              {accounts.map(a => (
                <Select.Option key={a.id} value={a.id}>{a.account_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="count"
            label="生成数量"
            initialValue={10}
          >
            <Input type="number" min={1} max={100} />
          </Form.Item>
        </Form>
      ),
      onOk: async () => {
        const accountId = form.getFieldValue('account_id') || accounts[0]?.id
        const count = form.getFieldValue('count') || 10
        try {
          const res = await api.post('/tasks/auto-generate', {
            account_id: accountId,
            count: parseInt(count)
          })
          message.success(res.data.message)
          fetchData()
        } catch (error) {
          message.error('生成失败')
        }
      }
    })
  }

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/tasks/${id}`)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleClearAll = async () => {
    try {
      await api.delete('/tasks')
      message.success('已清空所有任务')
      fetchData()
    } catch (error) {
      message.error('清空失败')
    }
  }

  const handleInitFromMaterials = async () => {
    if (accounts.length === 0) {
      message.warning('请先添加账号')
      return
    }

    Modal.confirm({
      title: '从素材初始化任务',
      content: (
        <Space direction="vertical">
          <p>将从素材库中读取视频、文案、话题，自动生成任务。</p>
          <Form form={form} layout="vertical">
            <Form.Item
              name="account_id"
              label="选择账号"
              rules={[{ required: true, message: '请选择账号' }]}
              initialValue={accounts[0]?.id}
            >
              <Select>
                {accounts.map(a => (
                  <Select.Option key={a.id} value={a.id}>{a.account_name}</Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item
              name="count"
              label="生成数量"
              initialValue={10}
            >
              <Input type="number" min={1} max={100} />
            </Form.Item>
          </Form>
        </Space>
      ),
      onOk: async () => {
        const accountId = form.getFieldValue('account_id') || accounts[0]?.id
        const count = form.getFieldValue('count') || 10
        try {
          const res = await api.post(`/tasks/init-from-materials?account_id=${accountId}&count=${count}`)
          message.success(res.data.message)
          fetchData()
        } catch (error) {
          message.error('初始化失败')
        }
      }
    })
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    pending: { color: 'default', text: '待发布' },
    running: { color: 'processing', text: '发布中' },
    success: { color: 'success', text: '已发布' },
    failed: { color: 'error', text: '失败' },
    paused: { color: 'warning', text: '已暂停' },
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: '账号',
      dataIndex: 'account_id',
      key: 'account_id',
      width: 120,
      render: (id: number) => accounts.find(a => a.id === id)?.account_name || `ID:${id}`,
    },
    {
      title: '视频',
      dataIndex: 'video_path',
      key: 'video_path',
      ellipsis: true,
      render: (path: string | null) => path ? (
        <span style={{ fontSize: 12 }}>{path.split(/[/\\]/).pop()}</span>
      ) : '-',
    },
    {
      title: '文案',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        const { color, text } = statusMap[status] || { color: 'default', text: status }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '发布时间',
      dataIndex: 'publish_time',
      key: 'publish_time',
      width: 160,
      render: (text: string | null) => text ? new Date(text).toLocaleString('zh-CN') : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: Task) => (
        <Button type="link" size="small" danger onClick={() => handleDelete(record.id)}>
          删除
        </Button>
      ),
    },
  ]

  return (
    <>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic title="总计" value={stats.total} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="待发布" value={stats.pending} valueStyle={{ color: '#999' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="今日发布" value={stats.today_success} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="发布成功" value={stats.success} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="发布失败" value={stats.failed} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="发布状态"
              value={publishStatus.status === 'running' ? '运行中' : publishStatus.status === 'paused' ? '已暂停' : '空闲'}
              valueStyle={{ color: publishStatus.status === 'running' ? '#3f8600' : '#999' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 控制按钮 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={20}>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加任务
            </Button>
            <Button icon={<ThunderboltOutlined />} onClick={handleAutoGenerate}>
              AI生成任务
            </Button>
            <Button icon={<SyncOutlined />} onClick={handleInitFromMaterials}>
              从素材初始化
            </Button>
            <Popconfirm title="确定清空所有任务？" onConfirm={handleClearAll}>
              <Button danger>清空所有</Button>
            </Popconfirm>
          </Space>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Space>
              <span>发布控制:</span>
              {publishStatus.status === 'running' ? (
                <Button size="small" icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>
                  暂停
                </Button>
              ) : (
                <Button type="primary" size="small" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>
                  开始
                </Button>
              )}
              <Button size="small" icon={<ReloadOutlined />} onClick={fetchData}>
                刷新
              </Button>
              <Button size="small" icon={<SwapOutlined />} onClick={handleShuffle}>
                乱序
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 15 }}
        size="small"
      />

      <Modal
        title="添加任务"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="account_id"
            label="关联账号"
            rules={[{ required: true, message: '请选择账号' }]}
          >
            <Select placeholder="请选择账号">
              {accounts.map(a => (
                <Select.Option key={a.id} value={a.id}>{a.account_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="video_path" label="视频路径">
            <Input placeholder="视频文件路径" />
          </Form.Item>
          <Form.Item name="content" label="文案">
            <Input.TextArea rows={3} placeholder="视频文案" />
          </Form.Item>
          <Form.Item name="topic" label="话题">
            <Input placeholder="话题标签，多个用逗号分隔" />
          </Form.Item>
          <Form.Item name="cover_path" label="封面路径">
            <Input placeholder="封面图片路径" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
