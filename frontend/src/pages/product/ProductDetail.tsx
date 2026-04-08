import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Descriptions, Tabs, Table, Typography, Space, Flex,
  Modal, Form, Input, message, Spin,
} from 'antd'
import { ArrowLeftOutlined, EditOutlined, LinkOutlined } from '@ant-design/icons'

import {
  useProductsV2, useUpdateProductV2,
  useVideos, useCopywritings,
} from '@/hooks'
import type { VideoResponse, CopywritingResponse } from '@/types/material'
import { formatSize, formatDuration } from '@/utils/format'
import { handleApiError } from '@/utils/error'

const { Title, Text } = Typography

interface EditFormValues {
  name: string
  link?: string
}

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const productId = id ? parseInt(id, 10) : undefined

  const [editOpen, setEditOpen] = useState(false)
  const [form] = Form.useForm<EditFormValues>()

  const { data: products = [], isLoading: productsLoading } = useProductsV2()
  const product = products.find((p) => p.id === productId)

  const { data: videos = [], isLoading: videosLoading } = useVideos({ productId })
  const { data: copywritings = [], isLoading: copywritingsLoading } = useCopywritings({ productId })

  const updateProduct = useUpdateProductV2()

  const handleEditOpen = useCallback(() => {
    if (!product) return
    form.setFieldsValue({ name: product.name, link: product.link ?? undefined })
    setEditOpen(true)
  }, [product, form])

  const handleEditSave = useCallback(async () => {
    try {
      const values = await form.validateFields()
      if (!productId) return
      await updateProduct.mutateAsync({ id: productId, ...values })
      message.success('更新商品成功')
      setEditOpen(false)
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      handleApiError(error, '更新商品失败')
    }
  }, [form, productId, updateProduct])

  const videoColumns = [
    {
      title: '视频名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (v: number | null) => formatSize(v),
    },
    {
      title: '时长',
      dataIndex: 'duration',
      key: 'duration',
      width: 80,
      render: (v: number | null) => formatDuration(v),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
  ]

  const copywritingColumns = [
    {
      title: '文案内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
  ]

  if (productsLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (!product) {
    return (
      <Flex vertical gap={24} style={{ padding: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
        <Text type="secondary">商品不存在</Text>
      </Flex>
    )
  }

  return (
    <Flex vertical gap={16} style={{ padding: 24 }}>
      <Space>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>返回</Button>
        <Title level={4} style={{ margin: 0 }}>{product.name}</Title>
      </Space>

      <Descriptions
        bordered
        size="small"
        extra={
          <Button icon={<EditOutlined />} onClick={handleEditOpen}>编辑</Button>
        }
      >
        <Descriptions.Item label="商品名称">{product.name}</Descriptions.Item>
        <Descriptions.Item label="商品链接">
          {product.link
            ? <Text type="secondary">{product.link}</Text>
            : <Text type="secondary">—</Text>
          }
        </Descriptions.Item>
        {product.dewu_url && (
          <Descriptions.Item label="得物链接">
            <Text type="secondary">{product.dewu_url}</Text>
          </Descriptions.Item>
        )}
        {product.description && (
          <Descriptions.Item label="商品描述" span={3}>
            {product.description}
          </Descriptions.Item>
        )}
        {product.image_url && (
          <Descriptions.Item label="图片链接">
            <Text type="secondary">{product.image_url}</Text>
          </Descriptions.Item>
        )}
        <Descriptions.Item label="创建时间">
          {new Date(product.created_at).toLocaleString('zh-CN')}
        </Descriptions.Item>
        <Descriptions.Item label="更新时间">
          {new Date(product.updated_at).toLocaleString('zh-CN')}
        </Descriptions.Item>
      </Descriptions>

      <Tabs
        items={[
          {
            key: 'videos',
            label: `关联视频 (${videos.length})`,
            children: (
              <Table<VideoResponse>
                dataSource={videos}
                rowKey="id"
                columns={videoColumns}
                loading={videosLoading}
                pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
                size="small"
              />
            ),
          },
          {
            key: 'copywritings',
            label: `关联文案 (${copywritings.length})`,
            children: (
              <Table<CopywritingResponse>
                dataSource={copywritings}
                rowKey="id"
                columns={copywritingColumns}
                loading={copywritingsLoading}
                pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
                size="small"
              />
            ),
          },
        ]}
      />

      <Modal
        title="编辑商品"
        open={editOpen}
        onOk={handleEditSave}
        confirmLoading={updateProduct.isPending}
        onCancel={() => setEditOpen(false)}
        destroyOnHidden
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
    </Flex>
  )
}
