import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Table, Button, Space, Tabs, Card, Typography, message,
  Modal, Form, Input, Select, Popconfirm, Upload, Tag, Empty, Statistic, Row, Col,
} from 'antd'
import type { UploadProps } from 'antd'
import {
  PlusOutlined, DeleteOutlined, ShopOutlined, UploadOutlined,
  LinkOutlined, SearchOutlined, GlobalOutlined, ScanOutlined, EditOutlined, ImportOutlined,
} from '@ant-design/icons'
import type { AxiosError } from 'axios'

import { useProductsV2, useCreateProductV2, useDeleteProductV2, useUpdateProductV2 } from '@/hooks'
import { useVideos, useCreateVideo, useDeleteVideo, useUploadVideo, useScanVideos, useBatchDeleteVideos } from '@/hooks'
import { useCopywritings, useCreateCopywriting, useDeleteCopywriting, useUpdateCopywriting, useImportCopywritings, useBatchDeleteCopywritings } from '@/hooks'
import { useCovers, useUploadCover, useDeleteCover, useBatchDeleteCovers } from '@/hooks'
import { useAudios, useUploadAudio, useDeleteAudio, useBatchDeleteAudios } from '@/hooks'
import { useTopics, useCreateTopic, useDeleteTopic, useSearchTopics, useGlobalTopics, useSetGlobalTopics, useBatchDeleteTopics } from '@/hooks'
import { api } from '@/services/api'

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
  const [editingProduct, setEditingProduct] = useState<ProductResponse | null>(null)
  const [form] = Form.useForm<ProductFormValues>()

  const { data: products = [], isLoading } = useProductsV2()
  const createProduct = useCreateProductV2()
  const deleteProduct = useDeleteProductV2()
  const updateProduct = useUpdateProductV2()

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
      if (
        error !== null &&
        typeof error === 'object' &&
        'errorFields' in error
      ) return
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
                  <Space>
                    <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(p)}>
                      编辑
                    </Button>
                    <Popconfirm title="确定删除此商品？" onConfirm={() => handleDelete(p.id)}>
                      <Button type="link" danger size="small" icon={<DeleteOutlined />}>
                        删除
                      </Button>
                    </Popconfirm>
                  </Space>
                </Space>
              </Card>
            ))}
          </Space>
        )}
      </Card>

      <Modal
        title={editingProduct ? "编辑商品" : "添加商品"}
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

// ─── Video tab ───────────────────────────────────────────────────────────────

interface VideoFormValues {
  name: string
  file_path: string
  product_id?: number
}

function VideoTab() {
  const [productFilter, setProductFilter] = useState<number | undefined>(undefined)
  const [uploadProductId, setUploadProductId] = useState<number | undefined>(undefined)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<VideoFormValues>()

  const { data: products = [] } = useProductsV2()
  const { data: videos = [], isLoading } = useVideos(productFilter)
  const createVideo = useCreateVideo()
  const deleteVideo = useDeleteVideo()
  const uploadVideo = useUploadVideo()
  const scanVideos = useScanVideos()

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

  const batchDeleteVideos = useBatchDeleteVideos()

  const handleBatchDelete = useCallback(async () => {
    const result = await batchDeleteVideos.mutateAsync(selectedIds)
    setSelectedIds([])
    message.success(`已删除 ${result.deleted} 个视频${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
  }, [selectedIds, batchDeleteVideos])

  const handleUpload = useCallback(async (options: Parameters<NonNullable<UploadProps['customRequest']>>[0]) => {
    try {
      await uploadVideo.mutateAsync({ file: options.file as File, productId: uploadProductId })
      message.success('视频上传成功')
      options.onSuccess?.({})
    } catch (error: unknown) {
      handleApiError(error, '视频上传失败')
      options.onError?.(new Error('上传失败') as never)
    }
  }, [uploadVideo, uploadProductId])

  const handleScan = useCallback(async () => {
    try {
      const result = await scanVideos.mutateAsync()
      Modal.info({
        title: '扫描导入完成',
        content: (
          <Space direction="vertical">
            <Text>扫描文件: {result.total_scanned}</Text>
            <Text>新导入: {result.new_imported}</Text>
            <Text>已跳过: {result.skipped}</Text>
            {result.failed > 0 && <Text type="danger">失败: {result.failed}</Text>}
          </Space>
        ),
      })
    } catch (error: unknown) {
      handleApiError(error, '扫描导入失败')
    }
  }, [scanVideos])

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'file_exists',
      key: 'file_exists',
      width: 60,
      render: (v: boolean) => v === false
        ? <Tag color="error">缺失</Tag>
        : <Tag color="success">正常</Tag>,
    },
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
        <Select
          allowClear
          placeholder="上传到商品"
          style={{ width: 160 }}
          options={productOptions}
          value={uploadProductId}
          onChange={setUploadProductId}
        />
        <Upload
          accept="video/mp4,video/quicktime"
          showUploadList={false}
          customRequest={handleUpload}
        >
          <Button icon={<UploadOutlined />} loading={uploadVideo.isPending}>
            上传视频
          </Button>
        </Upload>
        <Button icon={<ScanOutlined />} onClick={handleScan} loading={scanVideos.isPending}>
          扫描导入
        </Button>
        <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
          手动添加
        </Button>
        {selectedIds.length > 0 && (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger icon={<DeleteOutlined />}>批量删除 ({selectedIds.length})</Button>
          </Popconfirm>
        )}
      </Space>

      <Table<VideoResponse>
        dataSource={videos}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
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
  const [editingCw, setEditingCw] = useState<CopywritingResponse | null>(null)
  const [importProductId, setImportProductId] = useState<number | undefined>(undefined)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<CopywritingFormValues>()

  const { data: products = [] } = useProductsV2()
  const { data: copywritings = [], isLoading } = useCopywritings(productFilter)
  const createCopywriting = useCreateCopywriting()
  const deleteCopywriting = useDeleteCopywriting()
  const updateCopywriting = useUpdateCopywriting()
  const importCopywritings = useImportCopywritings()

  const productOptions = products.map((p: ProductResponse) => ({ label: p.name, value: p.id }))

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
      if (
        error !== null &&
        typeof error === 'object' &&
        'errorFields' in error
      ) return
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

  const batchDeleteCopywritings = useBatchDeleteCopywritings()

  const handleBatchDelete = useCallback(async () => {
    const result = await batchDeleteCopywritings.mutateAsync(selectedIds)
    setSelectedIds([])
    message.success(`已删除 ${result.deleted} 个文案${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
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
      <Space style={{ marginBottom: 12 }}>
        <Select
          allowClear
          placeholder="按商品筛选"
          style={{ width: 160 }}
          options={productOptions}
          value={productFilter}
          onChange={setProductFilter}
        />
        <Button icon={<PlusOutlined />} onClick={() => { setEditingCw(null); form.resetFields(); setAddModalOpen(true) }}>
          添加文案
        </Button>
        <Select
          allowClear
          placeholder="导入到商品"
          style={{ width: 140 }}
          options={productOptions}
          value={importProductId}
          onChange={setImportProductId}
        />
        <Upload accept=".txt" showUploadList={false} customRequest={handleImport}>
          <Button icon={<ImportOutlined />} loading={importCopywritings.isPending}>
            批量导入
          </Button>
        </Upload>
        {selectedIds.length > 0 && (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger icon={<DeleteOutlined />}>批量删除 ({selectedIds.length})</Button>
          </Popconfirm>
        )}
      </Space>

      <Table<CopywritingResponse>
        dataSource={copywritings}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
      />

      <Modal
        title={editingCw ? "编辑文案" : "添加文案"}
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
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const { data: covers = [], isLoading } = useCovers(videoFilter)
  const uploadCover = useUploadCover()
  const deleteCover = useDeleteCover()

  const handleUpload = useCallback(async (options: Parameters<NonNullable<UploadProps['customRequest']>>[0]) => {
    try {
      await uploadCover.mutateAsync({ file: options.file as File, videoId: videoFilter })
      message.success('封面上传成功')
      options.onSuccess?.({})
    } catch (error: unknown) {
      handleApiError(error, '封面上传失败')
      options.onError?.(new Error('上传失败') as never)
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

  const batchDeleteCovers = useBatchDeleteCovers()

  const handleBatchDelete = useCallback(async () => {
    const result = await batchDeleteCovers.mutateAsync(selectedIds)
    setSelectedIds([])
    message.success(`已删除 ${result.deleted} 个封面${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
  }, [selectedIds, batchDeleteCovers])

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
        {selectedIds.length > 0 && (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger icon={<DeleteOutlined />}>批量删除 ({selectedIds.length})</Button>
          </Popconfirm>
        )}
      </Space>

      <Table<CoverResponse>
        dataSource={covers}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
      />
    </>
  )
}

// ─── Audio tab ───────────────────────────────────────────────────────────────

function AudioTab() {
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const { data: audios = [], isLoading } = useAudios()
  const uploadAudio = useUploadAudio()
  const deleteAudio = useDeleteAudio()

  const handleUpload = useCallback(async (options: Parameters<NonNullable<UploadProps['customRequest']>>[0]) => {
    try {
      await uploadAudio.mutateAsync(options.file as File)
      message.success('音频上传成功')
      options.onSuccess?.({})
    } catch (error: unknown) {
      handleApiError(error, '音频上传失败')
      options.onError?.(new Error('上传失败') as never)
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

  const batchDeleteAudios = useBatchDeleteAudios()

  const handleBatchDelete = useCallback(async () => {
    const result = await batchDeleteAudios.mutateAsync(selectedIds)
    setSelectedIds([])
    message.success(`已删除 ${result.deleted} 个音频${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
  }, [selectedIds, batchDeleteAudios])

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
        {selectedIds.length > 0 && (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger icon={<DeleteOutlined />}>批量删除 ({selectedIds.length})</Button>
          </Popconfirm>
        )}
      </Space>

      <Table<AudioResponse>
        dataSource={audios}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
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
  const [globalModalOpen, setGlobalModalOpen] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [searchInput, setSearchInput] = useState<string>('')
  const [selectedGlobalIds, setSelectedGlobalIds] = useState<number[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<TopicFormValues>()

  const { data: topics = [], isLoading } = useTopics(sort)
  const { data: searchResults = [], isFetching: isSearching } = useSearchTopics(searchKeyword)
  const { data: globalTopicsData } = useGlobalTopics()
  const createTopic = useCreateTopic()
  const deleteTopic = useDeleteTopic()
  const setGlobalTopics = useSetGlobalTopics()

  const globalTopics = globalTopicsData?.topics ?? []

  const handleSearch = useCallback(() => {
    setSearchKeyword(searchInput.trim())
  }, [searchInput])

  const handleAddFromSearch = useCallback(async (topic: TopicResponse) => {
    // Add to library if not already present (topic already exists in /topics)
    // Just show success — the topic is already in the library from search
    message.success(`话题「${topic.name}」已在话题库中`)
  }, [])

  const handleOpenGlobalModal = useCallback(() => {
    setSelectedGlobalIds(globalTopicsData?.topic_ids ?? [])
    setGlobalModalOpen(true)
  }, [globalTopicsData])

  const handleSaveGlobalTopics = useCallback(async () => {
    try {
      await setGlobalTopics.mutateAsync({ topic_ids: selectedGlobalIds })
      message.success('全局话题设置成功')
      setGlobalModalOpen(false)
    } catch (error: unknown) {
      handleApiError(error, '设置全局话题失败')
    }
  }, [setGlobalTopics, selectedGlobalIds])

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

  const batchDeleteTopics = useBatchDeleteTopics()

  const handleBatchDelete = useCallback(async () => {
    const result = await batchDeleteTopics.mutateAsync(selectedIds)
    setSelectedIds([])
    message.success(`已删除 ${result.deleted} 个话题${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
  }, [selectedIds, batchDeleteTopics])

  const topicOptions = topics.map((t: TopicResponse) => ({ label: t.name, value: t.id }))

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
      {/* Search area */}
      <Card size="small" style={{ marginBottom: 12 }} title={<><SearchOutlined /> 搜索话题</>}>
        <Space style={{ marginBottom: 8 }}>
          <Input
            placeholder="输入关键词搜索话题"
            style={{ width: 240 }}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onPressEnter={handleSearch}
            allowClear
            onClear={() => { setSearchKeyword(''); setSearchInput('') }}
          />
          <Button icon={<SearchOutlined />} onClick={handleSearch} loading={isSearching}>
            搜索
          </Button>
        </Space>
        {searchKeyword && (
          isSearching ? (
            <Text type="secondary">搜索中…</Text>
          ) : searchResults.length === 0 ? (
            <Empty description="未找到相关话题" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <Space wrap>
              {searchResults.map((t: TopicResponse) => (
                <Space key={t.id} size={4}>
                  <Tag color="blue">{t.name}</Tag>
                  <Tag color="orange">{t.heat.toLocaleString()}</Tag>
                  <Button size="small" type="link" onClick={() => handleAddFromSearch(t)}>
                    添加
                  </Button>
                </Space>
              ))}
            </Space>
          )
        )}
      </Card>

      {/* Global topics area */}
      <Card
        size="small"
        style={{ marginBottom: 12 }}
        title={<><GlobalOutlined /> 全局话题</>}
        extra={
          <Button size="small" icon={<GlobalOutlined />} onClick={handleOpenGlobalModal}>
            设置全局话题
          </Button>
        }
      >
        {globalTopics.length === 0 ? (
          <Empty description="暂未设置全局话题" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Space wrap>
            {globalTopics.map((t: TopicResponse) => (
              <Tag key={t.id} color="geekblue">{t.name}</Tag>
            ))}
          </Space>
        )}
      </Card>

      {/* Topic library */}
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
        {selectedIds.length > 0 && (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger icon={<DeleteOutlined />}>批量删除 ({selectedIds.length})</Button>
          </Popconfirm>
        )}
      </Space>

      <Table<TopicResponse>
        dataSource={topics}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
      />

      {/* Add topic modal */}
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

      {/* Set global topics modal */}
      <Modal
        title="设置全局话题"
        open={globalModalOpen}
        onOk={handleSaveGlobalTopics}
        confirmLoading={setGlobalTopics.isPending}
        onCancel={() => setGlobalModalOpen(false)}
        destroyOnClose
        width={520}
      >
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          从话题库中选择话题作为全局默认话题，发布时自动附加。
        </Text>
        <Select
          mode="multiple"
          style={{ width: '100%' }}
          placeholder="选择话题（可多选）"
          options={topicOptions}
          value={selectedGlobalIds}
          onChange={setSelectedGlobalIds}
          filterOption={(input, option) =>
            (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
          }
        />
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
  const { data: stats } = useQuery<Record<string, number>>({
    queryKey: ['material-stats'],
    queryFn: async () => (await api.get('/system/material-stats')).data,
  })

  return (
    <>
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}><Card size="small"><Statistic title="视频" value={stats.videos} /></Card></Col>
          <Col span={4}><Card size="small"><Statistic title="文案" value={stats.copywritings} /></Card></Col>
          <Col span={4}><Card size="small"><Statistic title="封面" value={stats.covers} /></Card></Col>
          <Col span={4}><Card size="small"><Statistic title="音频" value={stats.audios} /></Card></Col>
          <Col span={4}><Card size="small"><Statistic title="话题" value={stats.topics} /></Card></Col>
          <Col span={4}><Card size="small"><Statistic title="商品覆盖率" value={stats.coverage_rate * 100} suffix="%" precision={0} /></Card></Col>
        </Row>
      )}
      <ProductSection />
      <Tabs defaultActiveKey="video" items={tabItems} />
    </>
  )
}
