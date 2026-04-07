import { useState, useCallback, useRef } from 'react'
import {
  Button, Space, Typography, message,
  Modal, Form, Input, Popconfirm, Upload, Tag,
} from 'antd'
import type { UploadProps } from 'antd'
import { PlusOutlined, ImportOutlined, DeleteOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'

import {
  useCreateCopywriting, useDeleteCopywriting,
  useUpdateCopywriting, useImportCopywritings, useBatchDeleteCopywritings,
} from '@/hooks'
import type { CopywritingResponse, CopywritingListResponse } from '@/types/material'
import { handleApiError } from '@/utils/error'
import { api } from '@/services/api'
import ProductSelect from '@/components/ProductSelect'

const SOURCE_TYPE_VALUE_ENUM = {
  manual: { text: 'manual' },
  import: { text: 'import' },
  ai_clip: { text: 'ai_clip' },
}

const { Text } = Typography

interface CopywritingFormValues {
  content: string
  product_id?: number
}

export default function CopywritingList() {
  const actionRef = useRef<ActionType>()
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [editingCw, setEditingCw] = useState<CopywritingResponse | null>(null)
  const [importProductId, setImportProductId] = useState<number | undefined>(undefined)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<CopywritingFormValues>()

  const createCopywriting = useCreateCopywriting()
  const deleteCopywriting = useDeleteCopywriting()
  const updateCopywriting = useUpdateCopywriting()
  const importCopywritings = useImportCopywritings()
  const batchDeleteCopywritings = useBatchDeleteCopywritings()

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      if (editingCw) {
        await updateCopywriting.mutateAsync({ id: editingCw.id, ...values })
        message.success('更新文案成功')
      } else {
        await createCopywriting.mutateAsync(values)
        message.success('添加文案成功')
      }
      setAddModalOpen(false)
      setEditingCw(null)
      form.resetFields()
      actionRef.current?.reload()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      handleApiError(error, editingCw ? '更新文案失败' : '添加文案失败')
    }
  }, [form, createCopywriting, updateCopywriting, editingCw])

  const handleEdit = useCallback((cw: CopywritingResponse) => {
    setEditingCw(cw)
    form.setFieldsValue({ content: cw.content, product_id: cw.product_id ?? undefined })
    setAddModalOpen(true)
  }, [form])

  const handleImport = useCallback(async (options: Parameters<NonNullable<UploadProps['customRequest']>>[0]) => {
    try {
      const result = await importCopywritings.mutateAsync({ file: options.file as File, productId: importProductId })
      message.success(`导入完成: ${result.imported} 条文案`)
      options.onSuccess?.({})
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '文案导入失败')
      options.onError?.(new Error('导入失败') as never)
    }
  }, [importCopywritings, importProductId])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteCopywriting.mutateAsync(id)
      message.success('删除成功')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除文案失败')
    }
  }, [deleteCopywriting])

  const handleBatchDelete = useCallback(async () => {
    try {
      const result = await batchDeleteCopywritings.mutateAsync(selectedIds)
      setSelectedIds([])
      message.success(`已删除 ${result.deleted} 个文案${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, batchDeleteCopywritings])

  const columns: ProColumns<CopywritingResponse>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 70,
      sorter: true,
      hideInSearch: true,
    },
    {
      title: '内容',
      dataIndex: 'content',
      ellipsis: true,
      render: (_, record) => (
        <Text>{record.content.substring(0, 80)}{record.content.length > 80 ? '…' : ''}</Text>
      ),
    },
    {
      title: '关联商品',
      dataIndex: 'product_name',
      width: 120,
      hideInSearch: true,
      render: (_, record) => record.product_name
        ? <Tag>{record.product_name}</Tag>
        : <Text type="secondary">—</Text>,
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      width: 100,
      valueEnum: SOURCE_TYPE_VALUE_ENUM,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      sorter: true,
      hideInSearch: true,
      render: (_, record) => new Date(record.created_at).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      hideInSearch: true,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small">删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <>
      <ProTable<CopywritingResponse>
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        request={async (params) => {
          const { data } = await api.get<CopywritingListResponse>('/copywritings', {
            params: {
              ...(params.content ? { keyword: params.content } : {}),
              ...(params.source_type ? { source_type: params.source_type } : {}),
            },
          })
          return { data: data.items, success: true, total: data.total }
        }}
        rowSelection={{
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        }}
        tableAlertOptionRender={() => (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger size="small" icon={<DeleteOutlined />} loading={batchDeleteCopywritings.isPending}>
              批量删除 ({selectedIds.length})
            </Button>
          </Popconfirm>
        )}
        toolBarRender={() => [
          <ProductSelect
            key="product-select"
            allowClear
            placeholder="导入到商品"
            style={{ width: 140 }}
            value={importProductId}
            onChange={(v) => setImportProductId(v as number | undefined)}
          />,
          <Upload key="import" accept=".txt" showUploadList={false} customRequest={handleImport}>
            <Button icon={<ImportOutlined />} loading={importCopywritings.isPending}>
              批量导入
            </Button>
          </Upload>,
          <Button
            key="add"
            icon={<PlusOutlined />}
            onClick={() => { setEditingCw(null); form.resetFields(); setAddModalOpen(true) }}
          >
            添加文案
          </Button>,
        ]}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        search={{ labelWidth: 'auto' }}
      />

      <Modal
        title={editingCw ? '编辑文案' : '添加文案'}
        open={addModalOpen}
        onOk={handleAdd}
        confirmLoading={editingCw ? updateCopywriting.isPending : createCopywriting.isPending}
        onCancel={() => { setAddModalOpen(false); setEditingCw(null); form.resetFields() }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="content" label="文案内容" rules={[{ required: true, message: '请输入文案内容' }]}>
            <Input.TextArea rows={4} placeholder="请输入文案内容" />
          </Form.Item>
          <Form.Item name="product_id" label="关联商品">
            <ProductSelect allowClear placeholder="选择商品" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
