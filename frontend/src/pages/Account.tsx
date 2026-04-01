import { useState } from 'react'
import { Table, Button, Space, Modal, Form, Input, message } from 'antd'
import { PlusOutlined, DeleteOutlined, LoginOutlined } from '@ant-design/icons'
import { useAccounts, useCreateAccount, useDeleteAccount } from '../hooks'
import LoginModal from '../components/LoginModal'
import StatusBadge from '../components/StatusBadge'

interface Account {
  id: number
  account_id: string
  account_name: string
  status: string
  last_login?: string | null
  created_at: string
}

export default function Account() {
  const [modalVisible, setModalVisible] = useState(false)
  const [loginModalVisible, setLoginModalVisible] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null)
  const [form] = Form.useForm()

  // 使用 React Query hooks
  const { data: accounts = [], isLoading, refetch } = useAccounts()
  const createAccount = useCreateAccount()
  const deleteAccount = useDeleteAccount()

  const handleAdd = () => {
    form.resetFields()
    setModalVisible(true)
  }

  // 打开登录弹窗
  const handleLoginClick = (record: Account) => {
    setSelectedAccount(record)
    setLoginModalVisible(true)
  }

  // 登录成功后刷新
  const handleLoginSuccess = () => {
    setLoginModalVisible(false)
    setSelectedAccount(null)
    refetch()
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      await createAccount.mutateAsync(values)
      message.success('添加账号成功')
      setModalVisible(false)
      refetch()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      message.error('添加失败')
    }
  }

  const handleDelete = async (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个账号吗？',
      onOk: async () => {
        await deleteAccount.mutateAsync(id)
        message.success('删除成功')
        refetch()
      },
    })
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
      render: (status: string) => <StatusBadge status={status} />,
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
      render: (_: unknown, record: Account) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<LoginOutlined />}
            onClick={() => handleLoginClick(record)}
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
        loading={isLoading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="添加账号"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => { setModalVisible(false); form.resetFields() }}
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

      {selectedAccount && (
        <LoginModal
          accountId={selectedAccount.id}
          accountName={selectedAccount.account_name}
          open={loginModalVisible}
          onSuccess={handleLoginSuccess}
          onCancel={() => { setLoginModalVisible(false); setSelectedAccount(null) }}
        />
      )}
    </>
  )
}
