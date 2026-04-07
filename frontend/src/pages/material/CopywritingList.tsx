import { useState, useCallback } from 'react'
import {
  Table, Button, Space, Typography, message,
  Modal, Form, Input, Popconfirm, Upload, Tag,
} from 'antd'
import type { UploadProps } from 'antd'
import { PlusOutlined, ImportOutlined } from '@ant-design/icons'

import {
  useCopywritings, useCreateCopywriting, useDeleteCopywriting,
  useUpdateCopywriting, useImportCopywritings, useBatchDeleteCopywritings,
} from '@/hooks'
import type { CopywritingResponse } from '@/types/material'
import { handleApiError } from '@/utils/error'
import ListPageLayout from '@/components/ListPageLayout'
import ProductSelect from '@/components/ProductSelect'
import BatchDeleteButton from '@/components/BatchDeleteButton'

const { Text } = Typography

interface CopywritingFormValues {
  content: string
  product_id?: number
}

export default function CopywritingList() {
  const [productFilter, setProductFilter] = useState<number | undefined>(undefined)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [editingCw, setEditingCw] = useState<CopywritingResponse | null>(null)
  const [importProductId, setImportProductId] = useState<number | undefined>(undefined)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<CopywritingFormValues>()

  const { data: copywritings = [], isLoading } = useCopywritings(productFilter)
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
    } catch (error: unknown) {
      handleApiError(error, '文案导入失败')
      options.onError?.(new Error('导入失败') as never)
    }
  }, [importCopywritings, importProductId])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteCopywriting.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      handleApiError(error, '删除文案失败')
    }
  }, [deleteCopywriting])

  const handleBatchDelete = useCallback(async () => {
    try {
      const result = await batchDeleteCopywritings.mutateAsync(selectedIds)
      setSelectedIds([])
      message.success(`已删除 ${result.deleted} 个文案${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, batchDeleteCopywritings])

  const columns = [
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (v: string) => <Text>{v.substring(0, 80)}{v.length > 80 ? '…' : ''}</Text>,
    },
    {
      title: '关联商品',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 120,
      render: (name: string | null) => name ? <Tag>{name}</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 80,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: unknown, record: CopywritingResponse) => (
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
      <ListPageLayout
        filterBar={
          <ProductSelect
            allowClear
            placeholder="按商品筛选"
            style={{ width: 160 }}
            value={productFilter}
            onChange={setProductFilter}
          />
        }
        actionBar={
          <Space>
            <ProductSelect
              allowClear
              placeholder="导入到商品"
              style={{ width: 140 }}
              value={importProductId}
              onChange={setImportProductId}
            />
            <Upload accept=".txt" showUploadList={false} customRequest={handleImport}>
              <Button icon={<ImportOutlined />} loading={importCopywritings.isPending}>
                批量导入
              </Button>
            </Upload>
            <Button
              icon={<PlusOutlined />}
              onClick={() => { setEditingCw(null); form.resetFields(); setAddModalOpen(true) }}
            >
              添加文案
            </Button>
            <BatchDeleteButton
              count={selectedIds.length}
              onConfirm={handleBatchDelete}
              loading={batchDeleteCopywritings.isPending}
            />
          </Space>
        }
      >
        <Table<CopywritingResponse>
          dataSource={copywritings}
          rowKey="id"
          columns={columns}
          loading={isLoading}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
          size="small"
          rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
        />
      </ListPageLayout>

      <Modal
        title={editingCw ? '编辑文案' : '添加文案'}
        open={addModalOpen}
        onOk={handleAdd}
        confirmLoading={editingCw ? updateCopywriting.isPending : createCopywriting.isPending}
        onCancel={() => { setAddModalOpen(false); form.resetFields() }}
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
