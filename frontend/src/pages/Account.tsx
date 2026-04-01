import { useEffect, useState } from 'react'
import { Table, Tag, Button, Space, Modal, Form, Input, message } from 'antd'
import { PlusOutlined, DeleteOutlined, LoginOutlined } from '@ant-design/icons'
import { api } from '../services/api'

interface Account {
  id: number
  account_id: string
  account_name: string
  status: string
  last_login: string | null
  created_at: string
}

export default function Account() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const res = await api.get('/accounts')
      setAccounts(res.data)
    } catch (error) {
      message.error('获取账号列表失败')
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
      await api.post('/accounts', values)
      message.success('添加账号成功')
      setModalVisible(false)
      fetchAccounts()
    } catch (error: any) {
      if (error.errorFields) return
      message.error(error.response?.data?.detail || '添加失败')
    }
  }

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个账号吗？',
      onOk: async () => {
        await api.delete(`/accounts/${id}`)
        message.success('删除成功')
        fetchAccounts()
      },
    })
  }

  const handleLogin = async (id: number) => {
    try {
      await api.post('/accounts/login', { account_id: accounts.find(a => a.id === id)?.account_id })
      message.info('请在新窗口中完成登录')
    } catch (error) {
      message.error('登录失败')
    }
  }

  const columns = [
    {
      title: '账号ID',
      dataIndex: 'account_id',
      key: 'account_id',
    },
    {
      title: '账号名称',
      dataIndex: 'account_name',
      key: 'account_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'active' ? 'green' : status === 'error' ? 'red' : 'default'
        const text = status === 'active' ? '活跃' : status === 'error' ? '异常' : '未激活'
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (text: string | null) => text ? new Date(text).toLocaleString('zh-CN') : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: Account) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<LoginOutlined />}
            onClick={() => handleLogin(record.id)}
          >
            登录
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加账号
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={accounts}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="添加账号"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="account_id"
            label="账号ID"
            rules={[{ required: true, message: '请输入账号ID' }]}
          >
            <Input placeholder="请输入得物账号ID" />
          </Form.Item>
          <Form.Item
            name="account_name"
            label="账号名称"
            rules={[{ required: true, message: '请输入账号名称' }]}
          >
            <Input placeholder="请输入显示名称" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
