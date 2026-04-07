import { useState, useCallback } from 'react'
import {
  Table, Button, Space, Typography, message,
  Modal, Form, Input, Popconfirm, Upload, Tag, Select,
} from 'antd'
import type { UploadProps } from 'antd'
import {
  PlusOutlined, UploadOutlined, ScanOutlined,
} from '@ant-design/icons'

import { useVideos, useCreateVideo, useDeleteVideo, useUploadVideo, useScanVideos, useBatchDeleteVideos } from '@/hooks'
import type { VideoResponse } from '@/types/material'
import { formatSize, formatDuration } from '@/utils/format'
import { handleApiError } from '@/utils/error'
import ListPageLayout from '@/components/ListPageLayout'
import ProductSelect from '@/components/ProductSelect'
import BatchDeleteButton from '@/components/BatchDeleteButton'

type FileStatusFilter = 'normal' | 'missing'

const { Text } = Typography

interface VideoFormValues {
  name: string
  file_path: string
  product_id?: number
}

export default function VideoList() {
  const [keyword, setKeyword] = useState<string | undefined>(undefined)
  const [fileStatusFilter, setFileStatusFilter] = useState<FileStatusFilter | undefined>(undefined)
  const [uploadProductId, setUploadProductId] = useState<number | undefined>(undefined)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<VideoFormValues>()

  const { data: rawVideos = [], isLoading } = useVideos({ keyword })
  const videos = fileStatusFilter === undefined
    ? rawVideos
    : rawVideos.filter((v) =>
        fileStatusFilter === 'normal' ? v.file_exists === true : v.file_exists === false
      )
  const createVideo = useCreateVideo()
  const deleteVideo = useDeleteVideo()
  const uploadVideo = useUploadVideo()
  const scanVideos = useScanVideos()
  const batchDeleteVideos = useBatchDeleteVideos()

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      await createVideo.mutateAsync(values)
      message.success('添加视频成功')
      setAddModalOpen(false)
      form.resetFields()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
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

  const handleBatchDelete = useCallback(async () => {
    try {
      const result = await batchDeleteVideos.mutateAsync(selectedIds)
      setSelectedIds([])
      message.success(`已删除 ${result.deleted} 个视频${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
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
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70, sorter: (a: VideoResponse, b: VideoResponse) => a.id - b.id },
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
      sorter: (a: VideoResponse, b: VideoResponse) => (a.file_size ?? 0) - (b.file_size ?? 0),
    },
    {
      title: '时长',
      dataIndex: 'duration',
      key: 'duration',
      width: 80,
      render: (v: number | null) => formatDuration(v),
      sorter: (a: VideoResponse, b: VideoResponse) => (a.duration ?? 0) - (b.duration ?? 0),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
      sorter: (a: VideoResponse, b: VideoResponse) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
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
      <ListPageLayout
        filterBar={
          <Space>
            <Input
              allowClear
              placeholder="搜索视频名称"
              style={{ width: 200 }}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value || undefined)}
            />
            <Select<FileStatusFilter>
              allowClear
              placeholder="文件状态"
              style={{ width: 140 }}
              value={fileStatusFilter}
              onChange={(v) => setFileStatusFilter(v)}
              onClear={() => setFileStatusFilter(undefined)}
              options={[
                { label: '正常', value: 'normal' },
                { label: '缺失', value: 'missing' },
              ]}
            />
          </Space>
        }
        actionBar={
          <Space>
            <ProductSelect
              allowClear
              placeholder="上传到商品"
              style={{ width: 160 }}
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
            <BatchDeleteButton
              count={selectedIds.length}
              onConfirm={handleBatchDelete}
              loading={batchDeleteVideos.isPending}
            />
          </Space>
        }
      >
        <Table<VideoResponse>
          dataSource={videos}
          rowKey="id"
          columns={columns}
          loading={isLoading}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
          size="small"
          rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
        />
      </ListPageLayout>

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
            <ProductSelect allowClear placeholder="选择商品" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
