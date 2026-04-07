import { useState, useCallback } from 'react'
import {
  Table, Button, Space, Tabs, Card, Typography, message,
  Modal, Form, Input, Select, Popconfirm, Upload, Tag, Empty,
} from 'antd'
import type { UploadProps } from 'antd'
import {
  PlusOutlined, DeleteOutlined, ShopOutlined, UploadOutlined,
  LinkOutlined,
} from '@ant-design/icons'
import type { AxiosError } from 'axios'

import { useProductsV2, useCreateProductV2, useDeleteProductV2 } from '@/hooks'
import { useVideos, useCreateVideo, useDeleteVideo } from '@/hooks'
import { useCopywritings, useCreateCopywriting, useDeleteCopywriting } from '@/hooks'
import { useCovers, useUploadCover, useDeleteCover } from '@/hooks'
import { useAudios, useUploadAudio, useDeleteAudio } from '@/hooks'
import { useTopics, useCreateTopic, useDeleteTopic } from '@/hooks'

import type {
  ProductResponse,
  VideoResponse,
  CopywritingResponse,
  CoverResponse,
  AudioResponse,
  TopicResponse,
} from '@/types/material'

const { Text } = Typography

// ─── helpers ────────────────────────────────────────────────────────────────

function formatSize(bytes: number | null): string {
  if (!bytes) return '—'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function handleApiError(error: unknown, fallback: string): void {
  const axiosErr = error as AxiosError<{ detail?: string }>
  if (axiosErr.isAxiosError) {
    message.error(axiosErr.response?.data?.detail ?? axiosErr.message)
  } else if (error instanceof Error) {
    message.error(error.message)
  } else {
    message.error(fallback)
  }
}

// ─── Product section ─────────────────────────────────────────────────────────

interface ProductFormValues {
  name: string
  link?: string
}

function ProductSection() {
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm<ProductFormValues>()

  const { data: products = [], isLoading } = useProductsV2()
  const createProduct = useCreateProductV2()
  const deleteProduct = useDeleteProductV2()

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      await createProduct.mutateAsync(values)
      message.success('添加商品成功')
      setModalOpen(false)
      form.resetFields()
    } catch (error: unknown) {
      if (
        error !== null &&
        typeof error === 'object' &&
        'errorFields' in error
      ) return
      handleApiError(error, '添加商品失败')
    }
  }, [form, createProduct])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteProduct.mutateAsync(id)
      message.success('删除商品成功')
    } catch (error: unknown) {
      handleApiError(error, '删除商品失败')
    }
  }, [deleteProduct])

  return (
    <>
      <Card
        title={<><ShopOutlined /> 商品管理</>}
        size="small"
        style={{ marginBottom: 16 }}
        loading={isLoading}
        extra={
          <Button
            size="small"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          >
            添加商品
          </Button>
        }
      >
        {products.length === 0 ? (
          <Empty description="暂无商品，点击「添加商品」开始" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Space wrap>
            {products.map((p: ProductResponse) => (
              <Card key={p.id} size="small" style={{ width: 200 }}>
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                  <Text strong ellipsis>{p.name}</Text>
                  {p.link && (
                    <Text type="secondary" style={{ fontSize: 12 }} ellipsis>
                      {p.link}
                    </Text>
                  )}
                  <Popconfirm title="确定删除此商品？" onConfirm={() => handleDelete(p.id)}>
                    <Button type="link" danger size="small" icon={<DeleteOutlined />}>
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              </Card>
            ))}
          </Space>
        )}
      </Card>

      <Modal
        title="添加商品"
        open={modalOpen}
        onOk={handleAdd}
        confirmLoading={createProduct.isPending}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
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

// ─── Video tab ───────────────────────────────────────────────────────────────

interface VideoFormValues {
  name: string
  file_path: string
  product_id?: number
}

function VideoTab() {
  const [productFilter, setProductFilter] = useState<number | undefined>(undefined)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [form] = Form.useForm<VideoFormValues>()

  const { data: products = [] } = useProductsV2()
  const { data: videos = [], isLoading } = useVideos(productFilter)
  const createVideo = useCreateVideo()
  const deleteVideo = useDeleteVideo()

  const productOptions = products.map((p: ProductResponse) => ({ label: p.name, value: p.id }))

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      await createVideo.mutateAsync(values)
      message.success('添加视频成功')
      setAddModalOpen(false)
      form.resetFields()
    } catch (error: unknown) {
      if (
        error !== null &&
        typeof error === 'object' &&
        'errorFields' in error
      ) return
      handleApiError(error, '添加视频失败')
    }
  }, [form, createVideo])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteVideo.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      handleApiError(error, '删除视频失败')
    }
  }, [deleteVideo])

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: '关联商品',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 120,
      render: (name: string | null) => name ? <Tag>{name}</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 90,
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
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: VideoResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        <Select
          allowClear
          placeholder="按商品筛选"
          style={{ width: 160 }}
          options={productOptions}
          value={productFilter}
          onChange={setProductFilter}
        />
        <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
          添加视频
        </Button>
      </Space>

      <Table<VideoResponse>
        dataSource={videos}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
      />

      <Modal
        title="添加视频"
        open={addModalOpen}
        onOk={handleAdd}
        confirmLoading={createVideo.isPending}
        onCancel={() => { setAddModalOpen(false); form.resetFields() }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="视频名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="视频名称" />
          </Form.Item>
          <Form.Item name="file_path" label="文件路径" rules={[{ required: true, message: '请输入文件路径' }]}>
            <Input placeholder="本地文件路径" />
          </Form.Item>
          <Form.Item name="product_id" label="关联商品">
            <Select allowClear placeholder="选择商品" options={productOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

// ─── Copywriting tab ─────────────────────────────────────────────────────────

interface CopywritingFormValues {
  content: string
  product_id?: number
}

function CopywritingTab() {
  const [productFilter, setProductFilter] = useState<number | undefined>(undefined)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [form] = Form.useForm<CopywritingFormValues>()

  const { data: products = [] } = useProductsV2()
  const { data: copywritings = [], isLoading } = useCopywritings(productFilter)
  const createCopywriting = useCreateCopywriting()
  const deleteCopywriting = useDeleteCopywriting()

  const productOptions = products.map((p: ProductResponse) => ({ label: p.name, value: p.id }))

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      await createCopywriting.mutateAsync(values)
      message.success('添加文案成功')
      setAddModalOpen(false)
      form.resetFields()
    } catch (error: unknown) {
      if (
        error !== null &&
        typeof error === 'object' &&
        'errorFields' in error
      ) return
      handleApiError(error, '添加文案失败')
    }
  }, [form, createCopywriting])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteCopywriting.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      handleApiError(error, '删除文案失败')
    }
  }, [deleteCopywriting])

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
      width: 80,
      render: (_: unknown, record: CopywritingResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        <Select
          allowClear
          placeholder="按商品筛选"
          style={{ width: 160 }}
          options={productOptions}
          value={productFilter}
          onChange={setProductFilter}
        />
        <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
          添加文案
        </Button>
      </Space>

      <Table<CopywritingResponse>
        dataSource={copywritings}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
      />

      <Modal
        title="添加文案"
        open={addModalOpen}
        onOk={handleAdd}
        confirmLoading={createCopywriting.isPending}
        onCancel={() => { setAddModalOpen(false); form.resetFields() }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="content" label="文案内容" rules={[{ required: true, message: '请输入文案内容' }]}>
            <Input.TextArea rows={4} placeholder="请输入文案内容" />
          </Form.Item>
          <Form.Item name="product_id" label="关联商品">
            <Select allowClear placeholder="选择商品" options={productOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

// ─── Cover tab ───────────────────────────────────────────────────────────────

function CoverTab() {
  const [videoFilter, setVideoFilter] = useState<number | undefined>(undefined)
  const { data: covers = [], isLoading } = useCovers(videoFilter)
  const uploadCover = useUploadCover()
  const deleteCover = useDeleteCover()

  const handleUpload: UploadProps['customRequest'] = useCallback(async ({ file, onSuccess, onError }) => {
    try {
      await uploadCover.mutateAsync({ file: file as File, videoId: videoFilter })
      message.success('封面上传成功')
      onSuccess?.({})
    } catch (error: unknown) {
      handleApiError(error, '封面上传失败')
      onError?.(new Error('上传失败'))
    }
  }, [uploadCover, videoFilter])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteCover.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      handleApiError(error, '删除封面失败')
    }
  }, [deleteCover])

  const columns = [
    { title: '文件路径', dataIndex: 'file_path', key: 'file_path', ellipsis: true },
    {
      title: '关联视频',
      dataIndex: 'video_id',
      key: 'video_id',
      width: 100,
      render: (v: number | null) => v ? <Tag>视频 #{v}</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 90,
      render: (v: number | null) => formatSize(v),
    },
    {
      title: '尺寸',
      key: 'dimensions',
      width: 100,
      render: (_: unknown, record: CoverResponse) =>
        record.width && record.height ? `${record.width}×${record.height}` : '—',
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
      width: 80,
      render: (_: unknown, record: CoverResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        <Input
          placeholder="视频ID筛选"
          style={{ width: 140 }}
          type="number"
          allowClear
          onChange={(e) => {
            const v = e.target.value
            setVideoFilter(v ? Number(v) : undefined)
          }}
        />
        <Upload
          accept="image/jpeg,image/png,image/webp"
          showUploadList={false}
          customRequest={handleUpload}
        >
          <Button icon={<UploadOutlined />} loading={uploadCover.isPending}>
            上传封面
          </Button>
        </Upload>
      </Space>

      <Table<CoverResponse>
        dataSource={covers}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
      />
    </>
  )
}

// ─── Audio tab ───────────────────────────────────────────────────────────────

function AudioTab() {
  const { data: audios = [], isLoading } = useAudios()
  const uploadAudio = useUploadAudio()
  const deleteAudio = useDeleteAudio()

  const handleUpload: UploadProps['customRequest'] = useCallback(async ({ file, onSuccess, onError }) => {
    try {
      await uploadAudio.mutateAsync(file as File)
      message.success('音频上传成功')
      onSuccess?.({})
    } catch (error: unknown) {
      handleApiError(error, '音频上传失败')
      onError?.(new Error('上传失败'))
    }
  }, [uploadAudio])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteAudio.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      handleApiError(error, '删除音频失败')
    }
  }, [deleteAudio])

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 90,
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
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: AudioResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        <Upload
          accept="audio/mpeg,audio/mp3,audio/wav,audio/aac,audio/ogg"
          showUploadList={false}
          customRequest={handleUpload}
        >
          <Button icon={<UploadOutlined />} loading={uploadAudio.isPending}>
            上传音频
          </Button>
        </Upload>
      </Space>

      <Table<AudioResponse>
        dataSource={audios}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
      />
    </>
  )
}

// ─── Topic tab ───────────────────────────────────────────────────────────────

interface TopicFormValues {
  name: string
  heat?: number
}

function TopicTab() {
  const [sort, setSort] = useState<string>('created_at')
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [form] = Form.useForm<TopicFormValues>()

  const { data: topics = [], isLoading } = useTopics(sort)
  const createTopic = useCreateTopic()
  const deleteTopic = useDeleteTopic()

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      await createTopic.mutateAsync(values)
      message.success('添加话题成功')
      setAddModalOpen(false)
      form.resetFields()
    } catch (error: unknown) {
      if (
        error !== null &&
        typeof error === 'object' &&
        'errorFields' in error
      ) return
      handleApiError(error, '添加话题失败')
    }
  }, [form, createTopic])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTopic.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      handleApiError(error, '删除话题失败')
    }
  }, [deleteTopic])

  const columns = [
    { title: '话题名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: '热度',
      dataIndex: 'heat',
      key: 'heat',
      width: 80,
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
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
      width: 80,
      render: (_: unknown, record: TopicResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <Space style={{ marginBottom: 12 }}>
        <Select
          value={sort}
          onChange={setSort}
          style={{ width: 120 }}
          options={[
            { label: '最新', value: 'created_at' },
            { label: '热度', value: 'heat' },
          ]}
        />
        <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
          添加话题
        </Button>
      </Space>

      <Table<TopicResponse>
        dataSource={topics}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
      />

      <Modal
        title="添加话题"
        open={addModalOpen}
        onOk={handleAdd}
        confirmLoading={createTopic.isPending}
        onCancel={() => { setAddModalOpen(false); form.resetFields() }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="话题名称" rules={[{ required: true, message: '请输入话题名称' }]}>
            <Input placeholder="话题名称" />
          </Form.Item>
          <Form.Item name="heat" label="热度">
            <Input type="number" placeholder="0" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────

const tabItems = [
  { key: 'video', label: '视频', children: <VideoTab /> },
  { key: 'copywriting', label: '文案', children: <CopywritingTab /> },
  { key: 'cover', label: '封面', children: <CoverTab /> },
  { key: 'audio', label: '音频', children: <AudioTab /> },
  { key: 'topic', label: '话题', children: <TopicTab /> },
]

export default function Material() {
  return (
    <>
      <ProductSection />
      <Tabs defaultActiveKey="video" items={tabItems} />
    </>
  )
}
