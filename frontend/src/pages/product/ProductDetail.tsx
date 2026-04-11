import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button, Tabs, Image, Tag, Space, message, Spin, Flex, Typography,
} from 'antd'
import { EditOutlined, SyncOutlined } from '@ant-design/icons'
import {
  PageContainer,
  ProDescriptions,
  ProTable,
  ModalForm,
  ProFormText,
} from '@ant-design/pro-components'
import type { ProColumns } from '@ant-design/pro-components'

import { useQueryClient } from '@tanstack/react-query'
import {
  useProduct,
  useParseProductMaterials,
  useUpdateProductV2,
} from '@/hooks'
import type { VideoResponse, CopywritingResponse } from '@/types/material'
import { formatSize, formatDuration } from '@/utils/format'
import { handleApiError } from '@/utils/error'
import { API_BASE } from '@/services/api'

const { Text } = Typography

interface EditFormValues {
  name: string
}

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const productId = id ? parseInt(id, 10) : undefined

  const [editOpen, setEditOpen] = useState(false)
  const [parsing, setParsing] = useState(false)

  const queryClient = useQueryClient()
  const { data: product, isLoading: productLoading } = useProduct(productId)
  const parseProductMaterials = useParseProductMaterials()

  const videos = product?.videos ?? []
  const covers = product?.covers ?? []
  const copywritings = product?.copywritings ?? []
  const topics = product?.topics ?? []

  const updateProduct = useUpdateProductV2()

  const handleEditSubmit = useCallback(async (values: EditFormValues) => {
    if (!productId) return false
    try {
      await updateProduct.mutateAsync({ id: productId, name: values.name })
      message.success('更新商品成功')
      return true
    } catch (error: unknown) {
      handleApiError(error, '更新商品失败')
      return false
    }
  }, [productId, updateProduct])

  const handleParse = useCallback(async () => {
    if (!productId) return
    setParsing(true)
    try {
      const data = await parseProductMaterials.mutateAsync(productId)
      message.success(`解析完成: ${(data.videos ?? []).length} 个视频, ${(data.covers ?? []).length} 张封面, ${(data.topics ?? []).length} 个话题`)
      queryClient.invalidateQueries({ queryKey: ['product', productId] })
    } catch (error: unknown) {
      handleApiError(error, '解析素材失败')
    } finally {
      setParsing(false)
    }
  }, [productId, parseProductMaterials, queryClient])

  const videoColumns: ProColumns<VideoResponse>[] = [
    { title: '视频名称', dataIndex: 'name', ellipsis: true },
    { title: '大小', dataIndex: 'file_size', width: 100, render: (_, r) => formatSize(r.file_size ?? null) },
    { title: '时长', dataIndex: 'duration', width: 80, render: (_, r) => formatDuration(r.duration ?? null) },
    {
      title: '创建时间', dataIndex: 'created_at', width: 160,
      render: (_, r) => new Date(r.created_at).toLocaleString('zh-CN'),
    },
  ]

  const copywritingColumns: ProColumns<CopywritingResponse>[] = [
    { title: '文案内容', dataIndex: 'content', ellipsis: true },
    { title: '来源', dataIndex: 'source_type', width: 100 },
    {
      title: '创建时间', dataIndex: 'created_at', width: 160,
      render: (_, r) => new Date(r.created_at).toLocaleString('zh-CN'),
    },
  ]

  if (productLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (!product) {
    return (
      <PageContainer title="商品不存在" onBack={() => navigate(-1)}>
        <Text type="secondary">商品不存在或已被删除</Text>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title={product.name}
      onBack={() => navigate(-1)}
      extra={[
        <Button
          key="parse"
          icon={<SyncOutlined />}
          loading={parsing}
          onClick={handleParse}
        >
          解析素材
        </Button>,
        <Button
          key="edit"
          type="primary"
          icon={<EditOutlined />}
          onClick={() => setEditOpen(true)}
        >
          编辑
        </Button>,
      ]}
    >
      <ProDescriptions<typeof product>
        dataSource={product}
        bordered
        size="small"
        column={2}
        columns={[
          { title: '商品名称', dataIndex: 'name' },
          {
            title: '解析状态',
            dataIndex: 'parse_status',
            render: (_, r) => {
              const map: Record<string, { label: string; color: string }> = {
                pending: { label: '待解析', color: 'default' },
                parsing: { label: '解析中', color: 'processing' },
                parsed: { label: '已解析', color: 'success' },
                error: { label: '解析失败', color: 'error' },
              }
              const entry = map[r.parse_status] ?? { label: r.parse_status, color: 'default' }
              return <Tag color={entry.color}>{entry.label}</Tag>
            },
          },
          {
            title: '创建时间',
            dataIndex: 'created_at',
            render: (_, r) => new Date(r.created_at).toLocaleString('zh-CN'),
          },
        ]}
      />

      <div style={{ marginTop: 16 }}>
        <Tabs
          items={[
            {
              key: 'videos',
              label: `视频 (${videos.length})`,
              children: (
                <ProTable<VideoResponse>
                  dataSource={videos}
                  rowKey="id"
                  columns={videoColumns}
                  search={false}
                  pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
                  size="small"
                  toolBarRender={false}
                />
              ),
            },
            {
              key: 'covers',
              label: `封面 (${covers.length})`,
              children: covers.length === 0 ? (
                <Flex justify="center" style={{ padding: 24 }}>
                  <Text type="secondary">暂无封面</Text>
                </Flex>
              ) : (
                <Image.PreviewGroup>
                  <Space wrap style={{ padding: 8 }}>
                    {covers.map((cover) => (
                      <Image
                        key={cover.id}
                        src={`${API_BASE}/covers/${cover.id}/image`}
                        width={120}
                        height={80}
                        style={{ objectFit: 'cover', borderRadius: 4 }}
                        fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                      />
                    ))}
                  </Space>
                </Image.PreviewGroup>
              ),
            },
            {
              key: 'copywritings',
              label: `文案 (${copywritings.length})`,
              children: (
                <ProTable<CopywritingResponse>
                  dataSource={copywritings}
                  rowKey="id"
                  columns={copywritingColumns}
                  search={false}
                  pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
                  size="small"
                  toolBarRender={false}
                />
              ),
            },
            {
              key: 'topics',
              label: `话题 (${topics.length})`,
              children: topics.length === 0 ? (
                <Flex justify="center" style={{ padding: 24 }}>
                  <Text type="secondary">暂无话题</Text>
                </Flex>
              ) : (
                <Space wrap style={{ padding: 8 }}>
                  {topics.map((topic) => (
                    <Tag key={topic.id} color="blue">
                      {topic.name}
                    </Tag>
                  ))}
                </Space>
              ),
            },
          ]}
        />
      </div>

      <ModalForm<EditFormValues>
        title="编辑商品"
        open={editOpen}
        onOpenChange={setEditOpen}
        onFinish={handleEditSubmit}
        initialValues={{ name: product.name }}
        modalProps={{ destroyOnHidden: true }}
      >
        <ProFormText
          name="name"
          label="商品名称"
          rules={[{ required: true, message: '请输入商品名称' }]}
          placeholder="请输入商品名称"
        />
      </ModalForm>
    </PageContainer>
  )
}
