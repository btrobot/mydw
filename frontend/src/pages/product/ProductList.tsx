import { useState, useCallback } from 'react'
import {
  Table, Button, Space, Typography, message,
  Modal, Form, Input, Popconfirm,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, LinkOutlined } from '@ant-design/icons'

import { useProductsV2, useCreateProductV2, useDeleteProductV2, useUpdateProductV2 } from '@/hooks'
import type { ProductResponse } from '@/types/material'
import { handleApiError } from '@/utils/error'
import ListPageLayout from '@/components/ListPageLayout'

const { Text } = Typography

interface ProductFormValues {
  name: string
  link?: string
}

export default function ProductList() {
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<ProductResponse | null>(null)
  const [searchText, setSearchText] = useState('')
  const [form] = Form.useForm<ProductFormValues>()

  const { data: products = [], isLoading } = useProductsV2()
  const createProduct = useCreateProductV2()
  const deleteProduct = useDeleteProductV2()
  const updateProduct = useUpdateProductV2()

  const filtered = products.filter((p: ProductResponse) =>
    p.name.toLowerCase().includes(searchText.toLowerCase())
  )

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      if (editingProduct) {
        await updateProduct.mutateAsync({ id: editingProduct.id, ...values })
        message.success('更新商品成功')
      } else {
        await createProduct.mutateAsync(values)
        message.success('添加商品成功')
      }
      setModalOpen(false)
      setEditingProduct(null)
      form.resetFields()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      handleApiError(error, editingProduct ? '更新商品失败' : '添加商品失败')
    }
  }, [form, createProduct, updateProduct, editingProduct])

  const handleEdit = useCallback((p: ProductResponse) => {
    setEditingProduct(p)
    form.setFieldsValue({ name: p.name, link: p.link ?? undefined })
    setModalOpen(true)
  }, [form])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteProduct.mutateAsync(id)
      message.success('删除商品成功')
    } catch (error: unknown) {
      handleApiError(error, '删除商品失败')
    }
  }, [deleteProduct])

  const columns = [
    {
      title: '商品名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '商品链接',
      dataIndex: 'link',
      key: 'link',
      ellipsis: true,
      render: (v: string | null) => v
        ? <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text>
        : <Text type="secondary">—</Text>,
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
      render: (_: unknown, record: ProductResponse) => (
        <Space>
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
    <>
      <ListPageLayout
        filterBar={
          <Input
            placeholder="搜索商品名称"
            style={{ width: 200 }}
            allowClear
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
          />
        }
        actionBar={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => { setEditingProduct(null); form.resetFields(); setModalOpen(true) }}
          >
            添加商品
          </Button>
        }
      >
        <Table<ProductResponse>
          dataSource={filtered}
          rowKey="id"
          columns={columns}
          loading={isLoading}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
          size="small"
        />
      </ListPageLayout>

      <Modal
        title={editingProduct ? '编辑商品' : '添加商品'}
        open={modalOpen}
        onOk={handleAdd}
        confirmLoading={createProduct.isPending || updateProduct.isPending}
        onCancel={() => { setModalOpen(false); setEditingProduct(null); form.resetFields() }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="商品名称"
            rules={[{ required: true, message: '请输入商品名称' }]}
          >
            <Input placeholder="请输入商品名称" />
          </Form.Item>
          <Form.Item name="link" label="商品链接">
            <Input placeholder="请输入得物商品链接" prefix={<LinkOutlined />} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
