import { useState, useCallback, useMemo } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  message,
  Row,
  Col,
  Typography,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  LinkOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { useAccounts, useCreateAccount, useDeleteAccount, useUpdateAccount } from '../hooks'
import type { AccountResponseExtended, AccountQueryParams } from '../hooks/useAccount'
import ConnectionModal from '../components/ConnectionModal'
import StatusBadge from '../components/StatusBadge'
import type { AccountCreate, AccountUpdate } from '@/api'

const { Text } = Typography

// -------------------------------------------------------------------
// Preset tag colors — cycling by tag index keeps colors stable
// -------------------------------------------------------------------
const TAG_COLORS = [
  'blue', 'green', 'orange', 'purple', 'cyan',
  'magenta', 'gold', 'volcano', 'geekblue', 'lime',
]

function tagColor(tag: string): string {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  }
  return TAG_COLORS[Math.abs(hash) % TAG_COLORS.length]
}

// -------------------------------------------------------------------
// AccountFormValues — shape of the Add Account modal form
// -------------------------------------------------------------------
interface AccountFormValues {
  account_id: string
  account_name: string
  tags?: string[]
  remark?: string
}

// -------------------------------------------------------------------
// AccountToolbar — search + tag-filter toolbar (extracted sub-component)
// -------------------------------------------------------------------
interface AccountToolbarProps {
  onSearch: (value: string) => void
  onTagChange: (value: string | undefined) => void
  tagOptions: string[]
  onAdd: () => void
}

function AccountToolbar({ onSearch, onTagChange, tagOptions, onAdd }: AccountToolbarProps) {
  return (
    <Row gutter={[12, 12]} style={{ marginBottom: 16 }} align="middle">
      <Col>
        <Button type="primary" icon={<PlusOutlined />} onClick={onAdd}>
          添加账号
        </Button>
      </Col>
      <Col flex="280px">
        <Input.Search
          placeholder="搜索账号名/昵称/备注"
          allowClear
          prefix={<SearchOutlined />}
          onSearch={onSearch}
          onChange={(e) => {
            // Trigger search when cleared via the × button (value becomes '')
            if (e.target.value === '') onSearch('')
          }}
        />
      </Col>
      <Col flex="180px">
        <Select
          allowClear
          placeholder="按标签筛选"
          style={{ width: '100%' }}
          onChange={(value: string | undefined) => onTagChange(value)}
          options={tagOptions.map((t) => ({ label: t, value: t }))}
        />
      </Col>
    </Row>
  )
}

// -------------------------------------------------------------------
// Inline remark editor cell
// -------------------------------------------------------------------
interface RemarkCellProps {
  value: string | null | undefined
  onSave: (remark: string) => void
}

function RemarkCell({ value, onSave }: RemarkCellProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value ?? '')

  const handleConfirm = useCallback(() => {
    onSave(draft)
    setEditing(false)
  }, [draft, onSave])

  const handleCancel = useCallback(() => {
    setDraft(value ?? '')
    setEditing(false)
  }, [value])

  if (editing) {
    return (
      <Input
        autoFocus
        size="small"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onPressEnter={handleConfirm}
        onBlur={handleCancel}
        style={{ width: 160 }}
      />
    )
  }

  return (
    <Text
      type="secondary"
      style={{ cursor: 'pointer', minWidth: 48, display: 'inline-block' }}
      title="点击编辑备注"
      onClick={() => { setDraft(value ?? ''); setEditing(true) }}
    >
      {value || <span style={{ color: '#bfbfbf' }}>--</span>}
    </Text>
  )
}

// -------------------------------------------------------------------
// Main Account page
// -------------------------------------------------------------------
export default function Account() {
  const [modalVisible, setModalVisible] = useState(false)
  const [connectionModalVisible, setConnectionModalVisible] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState<AccountResponseExtended | null>(null)
  const [form] = Form.useForm<AccountFormValues>()

  // Query params state
  const [queryParams, setQueryParams] = useState<AccountQueryParams>({})

  // React Query hooks
  const { data: accounts = [], isLoading, refetch } = useAccounts(queryParams)
  const createAccount = useCreateAccount()
  const deleteAccount = useDeleteAccount()
  const updateAccount = useUpdateAccount()

  // Derive unique tag options from all loaded accounts
  const tagOptions = useMemo<string[]>(() => {
    const set = new Set<string>()
    accounts.forEach((a) => (a.tags ?? []).forEach((t) => set.add(t)))
    return Array.from(set).sort()
  }, [accounts])

  // ---- Handlers ----
  const handleAdd = useCallback(() => {
    form.resetFields()
    setModalVisible(true)
  }, [form])

  const handleConnectClick = useCallback((record: AccountResponseExtended) => {
    setSelectedAccount(record)
    setConnectionModalVisible(true)
  }, [])

  const handleConnectionSuccess = useCallback(() => {
    setConnectionModalVisible(false)
    setSelectedAccount(null)
    refetch()
  }, [refetch])

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields()
      const payload: AccountCreate & { tags?: string[]; remark?: string } = {
        account_id: values.account_id,
        account_name: values.account_name,
        tags: values.tags,
        remark: values.remark,
      }
      await createAccount.mutateAsync(payload)
      message.success('添加账号成功')
      setModalVisible(false)
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      message.error('添加失败')
    }
  }, [form, createAccount])

  const handleDelete = useCallback((id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个账号吗？',
      onOk: async () => {
        await deleteAccount.mutateAsync(id)
        message.success('删除成功')
      },
    })
  }, [deleteAccount])

  const handleSaveRemark = useCallback((id: number, remark: string) => {
    const payload: AccountUpdate & { remark?: string } = { remark }
    updateAccount.mutateAsync({ accountId: id, data: payload }).then(() => {
      message.success('备注已保存')
    }).catch(() => {
      message.error('备注保存失败')
    })
  }, [updateAccount])

  // Search / filter
  const handleSearch = useCallback((value: string) => {
    setQueryParams((prev) => ({ ...prev, search: value || undefined }))
  }, [])

  const handleTagChange = useCallback((value: string | undefined) => {
    setQueryParams((prev) => ({ ...prev, tag: value || undefined }))
  }, [])

  // ---- Table columns ----
  const columns = useMemo(() => [
    {
      title: '账号ID',
      dataIndex: 'account_id',
      key: 'account_id',
      width: 140,
    },
    {
      title: '账号名称',
      dataIndex: 'account_name',
      key: 'account_name',
      width: 140,
    },
    {
      title: '平台昵称',
      dataIndex: 'dewu_nickname',
      key: 'dewu_nickname',
      width: 140,
      render: (text: string | null | undefined) =>
        text ? <Text>{text}</Text> : <Text type="secondary">--</Text>,
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags: string[] | undefined) => (
        <Space size={[4, 4]} wrap>
          {(tags ?? []).map((t) => (
            <Tag key={t} color={tagColor(t)}>{t}</Tag>
          ))}
          {(!tags || tags.length === 0) && <Text type="secondary">--</Text>}
        </Space>
      ),
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      width: 180,
      render: (remark: string | null | undefined, record: AccountResponseExtended) => (
        <RemarkCell
          value={remark}
          onSave={(value) => handleSaveRemark(record.id, value)}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => <StatusBadge status={status} />,
    },
    {
      title: '最后连接',
      dataIndex: 'last_login',
      key: 'last_login',
      width: 160,
      render: (text: string | null) =>
        text ? new Date(text).toLocaleString('zh-CN') : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: unknown, record: AccountResponseExtended) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<LinkOutlined />}
            onClick={() => handleConnectClick(record)}
          >
            连接
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
  ], [handleConnectClick, handleDelete, handleSaveRemark])

  return (
    <>
      <AccountToolbar
        onSearch={handleSearch}
        onTagChange={handleTagChange}
        tagOptions={tagOptions}
        onAdd={handleAdd}
      />

      <Table<AccountResponseExtended>
        columns={columns}
        dataSource={accounts}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1300 }}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />

      {/* Add account modal */}
      <Modal
        title="添加账号"
        open={modalVisible}
        onOk={handleSubmit}
        confirmLoading={createAccount.isPending}
        onCancel={() => { setModalVisible(false); form.resetFields() }}
        destroyOnClose
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
          <Form.Item name="tags" label="标签">
            <Select
              mode="tags"
              placeholder="输入或选择标签，按回车确认"
              options={tagOptions.map((t) => ({ label: t, value: t }))}
            />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea
              rows={3}
              placeholder="可选备注信息"
              maxLength={200}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Connection modal */}
      {selectedAccount && (
        <ConnectionModal
          accountId={selectedAccount.id}
          accountName={selectedAccount.account_name}
          phoneMasked={selectedAccount.phone_masked}
          open={connectionModalVisible}
          onSuccess={handleConnectionSuccess}
          onCancel={() => { setConnectionModalVisible(false); setSelectedAccount(null) }}
        />
      )}
    </>
  )
}
