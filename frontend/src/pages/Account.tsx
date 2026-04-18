import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  Dropdown,
  message,
  Row,
  Col,
  Typography,
  Tooltip,
  Alert,
} from 'antd'
import type { MenuProps } from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  LinkOutlined,
  SearchOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  SyncOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import {
  useAccounts,
  useBatchDeleteAccounts,
  useCreateAccount,
  useDeleteAccount,
  useUpdateAccount,
  usePreviewAccount,
  useClosePreview,
  usePreviewStatus,
  useHealthCheck,
  useBatchHealthCheck,
  useBatchCheckStatus,
} from '../hooks'
import type { AccountResponseExtended, AccountQueryParams, BatchHealthCheckResult } from '../hooks/useAccount'
import BatchDeleteButton from '../components/BatchDeleteButton'
import ConnectionModal from '../components/ConnectionModal'
import StatusBadge from '../components/StatusBadge'
import type { AccountCreate, AccountUpdate } from '@/api'
import { handleApiError } from '@/utils/error'

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
  selectedCount: number
  onBatchDelete: () => void
  batchDeleting: boolean
  onBatchCheck: () => void
  batchChecking: boolean
  batchProgress: number
  batchTotal: number
}

function AccountToolbar({
  onSearch,
  onTagChange,
  tagOptions,
  onAdd,
  selectedCount,
  onBatchDelete,
  batchDeleting,
  onBatchCheck,
  batchChecking,
  batchProgress,
  batchTotal,
}: AccountToolbarProps) {
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
      <Col flex="auto" style={{ textAlign: 'right' }}>
        <Space wrap>
          <BatchDeleteButton count={selectedCount} onConfirm={onBatchDelete} loading={batchDeleting} />
          <Button
            icon={batchChecking ? <LoadingOutlined /> : <SyncOutlined />}
            disabled={batchChecking}
            onClick={onBatchCheck}
          >
            {batchChecking ? `检查中 (${batchProgress}/${batchTotal})` : '批量检查连接'}
          </Button>
        </Space>
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
  const [checkingIds, setCheckingIds] = useState<Set<number>>(new Set())
  const [batchResult, setBatchResult] = useState<BatchHealthCheckResult | null>(null)
  const logPanelRef = useRef<HTMLDivElement>(null)

  // Query params state
  const [queryParams, setQueryParams] = useState<AccountQueryParams>({})
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  // React Query hooks
  const { data: accounts = [], isLoading, refetch } = useAccounts(queryParams)
  const createAccount = useCreateAccount()
  const deleteAccount = useDeleteAccount()
  const batchDeleteAccounts = useBatchDeleteAccounts()
  const updateAccount = useUpdateAccount()

  // Preview hooks
  const previewAccount = usePreviewAccount()
  const closePreview = useClosePreview()
  const { data: previewStatus } = usePreviewStatus()

  // Health check hooks
  const healthCheck = useHealthCheck()
  const batchHealthCheck = useBatchHealthCheck()
  const { data: batchStatus } = useBatchCheckStatus(batchHealthCheck.isPending)

  // Auto-scroll log panel to bottom when new logs arrive
  useEffect(() => {
    if (logPanelRef.current) {
      logPanelRef.current.scrollTop = logPanelRef.current.scrollHeight
    }
  }, [batchStatus?.logs])

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
        try {
          await deleteAccount.mutateAsync(id)
          message.success('删除成功')
          setSelectedIds((prev) => prev.filter((selectedId) => selectedId !== id))
        } catch (error: unknown) {
          handleApiError(error, '删除账号失败')
        }
      },
    })
  }, [deleteAccount])

  const handleBatchDelete = useCallback(async () => {
    try {
      const result = await batchDeleteAccounts.mutateAsync(selectedIds)
      setSelectedIds([])
      if (result.deleted > 0 && result.skipped === 0) {
        message.success(`已删除 ${result.deleted} 个账号`)
      } else if (result.deleted > 0 && result.skipped > 0) {
        message.warning(`已删除 ${result.deleted} 个账号，${result.skipped} 个账号因存在关联任务/发布记录被跳过`)
      } else if (result.skipped > 0) {
        message.warning(`未删除任何账号：${result.skipped} 个账号因存在关联任务/发布记录被跳过`)
      } else {
        message.info('没有账号被删除')
      }
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [batchDeleteAccounts, selectedIds])

  const handleSaveRemark = useCallback((id: number, remark: string) => {
    const payload: AccountUpdate & { remark?: string } = { remark }
    updateAccount.mutateAsync({ accountId: id, data: payload }).then(() => {
      message.success('备注已保存')
    }).catch(() => {
      message.error('备注保存失败')
    })
  }, [updateAccount])

  // ---- Preview handlers ----
  const handlePreview = useCallback(async (id: number) => {
    try {
      await previewAccount.mutateAsync(id)
      message.success('预览浏览器已打开')
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'message' in error) {
        message.error((error as Error).message || '打开预览失败')
      } else {
        message.error('打开预览失败')
      }
    }
  }, [previewAccount])

  const handleClosePreview = useCallback((id: number, saveSession: boolean) => {
    closePreview.mutateAsync({ accountId: id, saveSession }).then(() => {
      message.success(saveSession ? 'Session 已保存，预览已关闭' : '预览已关闭')
      refetch()
    }).catch((error: unknown) => {
      if (error !== null && typeof error === 'object' && 'message' in error) {
        message.error((error as Error).message || '关闭预览失败')
      } else {
        message.error('关闭预览失败')
      }
    })
  }, [closePreview, refetch])

  // Search / filter
  const handleSearch = useCallback((value: string) => {
    setQueryParams((prev) => ({ ...prev, search: value || undefined }))
  }, [])

  const handleTagChange = useCallback((value: string | undefined) => {
    setQueryParams((prev) => ({ ...prev, tag: value || undefined }))
  }, [])

  const handleHealthCheck = useCallback(async (record: AccountResponseExtended) => {
    setCheckingIds(prev => new Set(prev).add(record.id))
    try {
      const result = await healthCheck.mutateAsync(record.id)
      if (result.is_valid) {
        message.success('Session 有效')
      } else {
        message.warning('Session 已过期，请重新登录')
      }
    } catch {
      message.error('检查失败，请稍后重试')
    } finally {
      setCheckingIds(prev => {
        const next = new Set(prev)
        next.delete(record.id)
        return next
      })
    }
  }, [healthCheck])

  const handleBatchCheck = useCallback(async () => {
    try {
      const result = await batchHealthCheck.mutateAsync()
      setBatchResult(result)
      setTimeout(() => setBatchResult(null), 8000)
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'message' in error) {
        message.error((error as Error).message || '批量检查失败')
      } else {
        message.error('批量检查失败')
      }
    }
  }, [batchHealthCheck])

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
      width: 200,
      fixed: 'right' as const,
      render: (_: unknown, record: AccountResponseExtended) => {
        const canPreview = record.status === 'active' || record.status === 'session_expired'
        const isThisPreviewOpen = previewStatus?.is_open && previewStatus.account_id === record.id
        const isOtherPreviewOpen = previewStatus?.is_open && previewStatus.account_id !== record.id

        const closeMenuItems: MenuProps['items'] = [
          {
            key: 'save-close',
            label: '保存并关闭',
            onClick: () => handleClosePreview(record.id, true),
          },
          {
            key: 'close-only',
            label: '直接关闭',
            onClick: () => handleClosePreview(record.id, false),
          },
        ]

        const isChecking = checkingIds.has(record.id)

        let connectButton = null
        if (record.status === 'logging_in') {
          connectButton = (
            <Button type="link" size="small" icon={<LinkOutlined />} disabled>
              连接中
            </Button>
          )
        } else if (record.status === 'active') {
          connectButton = (
            <Button
              type="link"
              size="small"
              icon={<SyncOutlined spin={isChecking} />}
              loading={isChecking}
              disabled={isChecking}
              onClick={() => handleHealthCheck(record)}
            >
              检查连接
            </Button>
          )
        } else if (record.status === 'session_expired' || record.status === 'error') {
          connectButton = (
            <Button
              type="link"
              size="small"
              icon={<LinkOutlined />}
              onClick={() => handleConnectClick(record)}
            >
              重新登录
            </Button>
          )
        } else if (record.status !== 'disabled') {
          connectButton = (
            <Button
              type="link"
              size="small"
              icon={<LinkOutlined />}
              onClick={() => handleConnectClick(record)}
            >
              连接
            </Button>
          )
        }

        return (
          <Space>
            {connectButton}
            {canPreview && (
              isThisPreviewOpen ? (
                <Dropdown menu={{ items: closeMenuItems }} trigger={['click']}>
                  <Button
                    type="link"
                    size="small"
                    icon={<EyeInvisibleOutlined />}
                    loading={closePreview.isPending}
                  >
                    关闭预览
                  </Button>
                </Dropdown>
              ) : (
                <Tooltip
                  title={isOtherPreviewOpen ? '请先关闭当前预览' : undefined}
                >
                  <Button
                    type="link"
                    size="small"
                    icon={<EyeOutlined />}
                    disabled={isOtherPreviewOpen}
                    loading={previewAccount.isPending && previewAccount.variables === record.id}
                    onClick={() => handlePreview(record.id)}
                  >
                    预览
                  </Button>
                </Tooltip>
              )
            )}
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
        )
      },
    },
  ], [
    handleConnectClick,
    handleDelete,
    handleSaveRemark,
    handlePreview,
    handleClosePreview,
    handleHealthCheck,
    previewStatus,
    previewAccount.isPending,
    previewAccount.variables,
    closePreview.isPending,
    checkingIds,
  ])

  return (
    <>
      <AccountToolbar
        onSearch={handleSearch}
        onTagChange={handleTagChange}
        tagOptions={tagOptions}
        onAdd={handleAdd}
        selectedCount={selectedIds.length}
        onBatchDelete={handleBatchDelete}
        batchDeleting={batchDeleteAccounts.isPending}
        onBatchCheck={handleBatchCheck}
        batchChecking={batchHealthCheck.isPending}
        batchProgress={batchStatus?.progress ?? 0}
        batchTotal={batchStatus?.total ?? 0}
      />

      {batchResult && (
        <Alert
          style={{ marginBottom: 16 }}
          type={batchResult.expired_count > 0 || batchResult.error_count > 0 ? 'warning' : 'success'}
          message={`批量检查完成：${batchResult.valid_count} 个有效，${batchResult.expired_count} 个已过期，${batchResult.error_count} 个异常`}
          closable
          onClose={() => setBatchResult(null)}
          showIcon
        />
      )}

      {(batchStatus?.in_progress || (batchStatus?.logs && batchStatus.logs.length > 0)) && (
        <div
          ref={logPanelRef}
          style={{
            marginBottom: 16,
            padding: '8px 12px',
            background: '#fafafa',
            border: '1px solid #f0f0f0',
            borderRadius: 6,
            maxHeight: 200,
            overflowY: 'auto',
            fontSize: 13,
            fontFamily: 'monospace',
          }}
        >
          {(batchStatus.logs ?? []).map((log, i) => (
            <div
              key={i}
              style={{
                padding: '2px 0',
                color: log.includes('[ERROR]') ? '#ff4d4f' : log.includes('[EXPIRED]') ? '#faad14' : '#52c41a',
              }}
            >
              {log}
            </div>
          ))}
          {batchStatus.in_progress && batchStatus.current_account_name && (
            <div style={{ padding: '2px 0', color: '#1890ff' }}>
              [{(batchStatus.progress ?? 0) + 1}/{batchStatus.total}] {batchStatus.current_account_name} - 检查中...
            </div>
          )}
        </div>
      )}

      <Table<AccountResponseExtended>
        columns={columns}
        dataSource={accounts}
        rowKey="id"
        rowSelection={{
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        }}
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
        destroyOnHidden
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
