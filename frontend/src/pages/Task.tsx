import { useEffect, useState } from 'react'
import {
  Table, Tag, Button, Space, Modal, Form, Input, Select,
  DatePicker, message, Popconfirm, Row, Col, Card
} from 'antd'
import {
  PlusOutlined, PlayCircleOutlined, PauseCircleOutlined,
  ReloadOutlined, DeleteOutlined, SwapOutlined
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
  created_at: string
}

interface Account {
  id: number
  account_name: string
}

export default function Task() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [publishStatus, setPublishStatus] = useState<'idle' | 'running' | 'paused'>('idle')
  const [form] = Form.useForm()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [tasksRes, accountsRes, publishRes] = await Promise.all([
        api.get('/tasks'),
        api.get('/accounts'),
        api.get('/publish/status'),
      ])
      setTasks(tasksRes.data.items || [])
      setAccounts(accountsRes.data)
      setPublishStatus(publishRes.data.status)
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
      await api.post('/publish/shuffle')
      message.success('任务顺序已打乱')
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    await api.delete(`/tasks/${id}`)
    message.success('删除成功')
    fetchData()
  }

  const handleClearAll = async () => {
    await api.delete('/tasks')
    message.success('已清空所有任务')
    fetchData()
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
      title: '账号ID',
      dataIndex: 'account_id',
      key: 'account_id',
      width: 100,
      render: (id: number) => accounts.find(a => a.id === id)?.account_name || id,
    },
    {
      title: '视频路径',
      dataIndex: 'video_path',
      key: 'video_path',
      ellipsis: true,
    },
    {
      title: '文案',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
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
        <Space>
          <Button type="link" size="small" onClick={() => handleDelete(record.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={16}>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加任务
            </Button>
            <Popconfirm title="确定清空所有任务？" onConfirm={handleClearAll}>
              <Button danger>清空所有任务</Button>
            </Popconfirm>
          </Space>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Space>
              <span>发布状态: </span>
              <Tag color={publishStatus === 'running' ? 'green' : publishStatus === 'paused' ? 'orange' : 'default'}>
                {publishStatus === 'idle' ? '空闲' : publishStatus === 'running' ? '运行中' : '已暂停'}
              </Tag>
              {publishStatus === 'running' ? (
                <Button icon={<PauseCircleOutlined />} onClick={() => handlePublish('pause')}>
                  暂停
                </Button>
              ) : (
                <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => handlePublish('start')}>
                  开始发布
                </Button>
              )}
              <Button icon={<ReloadOutlined />} onClick={fetchData}>
                刷新
              </Button>
              <Button icon={<SwapOutlined />} onClick={handleShuffle}>
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
