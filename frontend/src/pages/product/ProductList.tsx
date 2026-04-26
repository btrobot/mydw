import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button, Space, Typography, message,
  Modal, Form, Input, Popconfirm,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'
import { listProductsApiProductsGet } from '@/api'

import { InlineNotice } from '@/components/feedback/InlineNotice'
import { PageHeader } from '@/components/ui/PageHeader'
import { useCreateProductV2, useDeleteProductV2, useUpdateProductV2, useBatchDeleteProducts, useParseProductMaterials } from '@/hooks'
import type { ProductResponse, ProductListResponse, ParseStatus } from '@/types/material'
import { handleApiError } from '@/utils/error'

const { Link } = Typography

interface ProductCreateValues {
  name: string
  share_text: string
}

interface ProductEditValues {
  name: string
}


export default function ProductList() {
  const navigate = useNavigate()
  const actionRef = useRef<ActionType>()
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<ProductResponse | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<ProductCreateValues | ProductEditValues>()

  const [parsingIds, setParsingIds] = useState<Set<number>>(new Set())

  const createProduct = useCreateProductV2()
  const deleteProduct = useDeleteProductV2()
  const updateProduct = useUpdateProductV2()
  const batchDeleteProducts = useBatchDeleteProducts()
  const parseProductMaterials = useParseProductMaterials()

  const handleAdd = useCallback(async () => {
    try {
      if (editingProduct) {
        const values = await form.validateFields() as ProductEditValues
        await updateProduct.mutateAsync({ id: editingProduct.id, name: values.name })
        message.success('更新商品成功')
      } else {
        const values = await form.validateFields() as ProductCreateValues
        await createProduct.mutateAsync({ name: values.name, share_text: values.share_text })
        message.success('添加商品成功')
      }
      setModalOpen(false)
      setEditingProduct(null)
      form.resetFields()
      actionRef.current?.reload()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      handleApiError(error, editingProduct ? '更新商品失败' : '添加商品失败')
    }
  }, [form, createProduct, updateProduct, editingProduct])

  const handleEdit = useCallback((p: ProductResponse) => {
    setEditingProduct(p)
    form.setFieldsValue({ name: p.name })
    setModalOpen(true)
  }, [form])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteProduct.mutateAsync(id)
      message.success('删除商品成功')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除商品失败')
    }
  }, [deleteProduct])

  const handleBatchDelete = useCallback(async () => {
    try {
      await batchDeleteProducts.mutateAsync(selectedIds)
      setSelectedIds([])
      message.success(`已删除 ${selectedIds.length} 个商品`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, batchDeleteProducts])

  const handleParse = useCallback(async (id: number) => {
    setParsingIds((prev) => new Set(prev).add(id))
    try {
      const data = await parseProductMaterials.mutateAsync(id)
      message.success(`解析完成: ${(data.videos ?? []).length} 个视频, ${(data.covers ?? []).length} 张封面, ${(data.topics ?? []).length} 个话题`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '解析素材失败')
    } finally {
      setParsingIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }, [parseProductMaterials])

  const columns: ProColumns<ProductResponse>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 70,
      sorter: true,
      hideInSearch: true,
    },
    {
      title: '商品名称',
      dataIndex: 'name',
      ellipsis: true,
      render: (_, record) => (
        <Link onClick={() => navigate(`/material/product/${record.id}`)}>{record.name}</Link>
      ),
    },
    {
      title: '解析状态',
      dataIndex: 'parse_status',
      width: 100,
      hideInSearch: true,
      valueEnum: {
        pending: { text: '待解析', status: 'Default' },
        parsing: { text: '解析中', status: 'Processing' },
        parsed: { text: '已解析', status: 'Success' },
        error: { text: '解析失败', status: 'Error' },
      } satisfies Record<ParseStatus, { text: string; status: string }>,
    },
    {
      title: '视频数',
      dataIndex: 'video_count',
      width: 80,
      hideInSearch: true,
    },
    {
      title: '文案数',
      dataIndex: 'copywriting_count',
      width: 80,
      hideInSearch: true,
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
      width: 180,
      hideInSearch: true,
      render: (_, record) => (
        <Space>
          {record.parse_status === 'error' && (
            <Button
              type="link"
              size="small"
              icon={<SyncOutlined />}
              loading={parsingIds.has(record.id)}
              onClick={() => handleParse(record.id)}
            >
              重新解析
            </Button>
          )}
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确定删除此商品？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <PageHeader
        title="\u5546\u54c1\u7ba1\u7406"
        subtitle="\u5c06\u5546\u54c1\u5217\u8868\u4f5c\u4e3a\u7d20\u6750\u89e3\u6790\u3001\u72b6\u6001\u8ffd\u8e2a\u4e0e\u8d44\u4ea7\u8986\u76d6\u60c5\u51b5\u7684\u5165\u53e3\uff0c\u8ba9\u521b\u5efa\u3001\u7f16\u8f91\u548c\u91cd\u8bd5\u5728\u540c\u4e00\u5c42\u7ea7\u5185\u5b8c\u6210\u3002"
        extra={(
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => { setEditingProduct(null); form.resetFields(); setModalOpen(true) }}
          >
            {'\u6dfb\u52a0\u5546\u54c1'}
          </Button>
        )}
      />
      <InlineNotice
        message="\u89e3\u6790\u5931\u8d25\u7684\u5546\u54c1\u4f1a\u5728\u5f53\u524d\u5217\u8868\u4e2d\u76f4\u63a5\u66b4\u9732\uff0c\u4fbf\u4e8e\u5feb\u901f\u91cd\u8bd5\u548c\u4fee\u6b63"
        description="\u672c\u9875\u4f18\u5148\u627f\u8f7d\u5546\u54c1\u7d20\u6750\u7684\u51c6\u5165\u4e0e\u89e3\u6790\u72b6\u6001\u7ba1\u7406\uff0c\u5177\u4f53\u7d20\u6750\u5185\u5bb9\u4ecd\u4ece\u5546\u54c1\u8be6\u60c5\u9875\u8fdb\u5165\u5904\u7406\u3002"
      />
      <ProTable<ProductResponse>
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        headerTitle={false}
        request={async (params) => {
          const response = await listProductsApiProductsGet({
            query: params.name ? { name: params.name as string } : undefined,
          })
          const data = response.data as ProductListResponse
          return { data: data.items, success: true, total: data.total }
        }}
        rowSelection={{
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        }}
        tableAlertOptionRender={() => (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger size="small" icon={<DeleteOutlined />} loading={batchDeleteProducts.isPending}>
              批量删除 ({selectedIds.length})
            </Button>
          </Popconfirm>
        )}
        toolBarRender={false}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        search={{ labelWidth: 'auto' }}
      />

      <Modal
        title={editingProduct ? '编辑商品' : '添加商品'}
        open={modalOpen}
        onOk={handleAdd}
        confirmLoading={createProduct.isPending || updateProduct.isPending}
        onCancel={() => { setModalOpen(false); setEditingProduct(null); form.resetFields() }}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          {editingProduct ? (
            <Form.Item
              name="name"
              label="商品名称"
              rules={[{ required: true, message: '请输入商品名称' }]}
            >
              <Input placeholder="请输入商品名称" />
            </Form.Item>
          ) : (
            <>
              <Form.Item
                name="name"
                label="商品名称"
                rules={[{ required: true, message: '请输入商品名称' }]}
              >
                <Input placeholder="请输入商品名称" />
              </Form.Item>
              <Form.Item
                name="share_text"
                label="分享文本"
                rules={[{ required: true, message: '请输入分享文本' }]}
              >
                <Input.TextArea placeholder="粘贴得物分享文本或链接" rows={3} />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </Space>
  )
}
