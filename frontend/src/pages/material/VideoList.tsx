import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Button, Space, Typography, message,
  Modal, Form, Input, Popconfirm, Upload, Tag,
} from 'antd'
import type { UploadProps } from 'antd'
import {
  PlusOutlined, UploadOutlined, ScanOutlined, DeleteOutlined, PlayCircleOutlined,
} from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'
import { listVideosApiVideosGet } from '@/api'

import { InlineNotice } from '@/components/feedback/InlineNotice'
import { PageHeader } from '@/components/ui/PageHeader'
import { useCreateVideo, useDeleteVideo, useUploadVideo, useScanVideos, useBatchDeleteVideos } from '@/hooks'
import type { VideoResponse, VideoListResponse } from '@/types/material'
import { formatSize, formatDuration } from '@/utils/format'
import { handleApiError } from '@/utils/error'
import { API_BASE } from '@/services/api'
import ProductSelect from '@/components/ProductSelect'

const { Text } = Typography

interface VideoFormValues {
  name: string
  file_path: string
  product_id?: number
}

export default function VideoList() {
  const navigate = useNavigate()
  const actionRef = useRef<ActionType>()
  const [uploadProductId, setUploadProductId] = useState<number | undefined>(undefined)
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [playingVideo, setPlayingVideo] = useState<VideoResponse | null>(null)
  const [form] = Form.useForm<VideoFormValues>()

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
      actionRef.current?.reload()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      handleApiError(error, '添加视频失败')
    }
  }, [form, createVideo])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteVideo.mutateAsync(id)
      message.success('删除成功')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除视频失败')
    }
  }, [deleteVideo])

  const handleBatchDelete = useCallback(async () => {
    try {
      const result = await batchDeleteVideos.mutateAsync(selectedIds)
      setSelectedIds([])
      if (result.deleted > 0 && result.skipped === 0) {
        message.success(`已删除 ${result.deleted} 个视频`)
      } else if (result.deleted > 0 && result.skipped > 0) {
        message.warning(`已删除 ${result.deleted} 个视频，${result.skipped} 个视频因存在任务引用被跳过`)
      } else if (result.skipped > 0) {
        message.warning(`未删除任何视频：${result.skipped} 个视频因存在任务引用被跳过`)
      } else {
        message.info('没有视频被删除')
      }
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, batchDeleteVideos])

  const handleUpload = useCallback(async (options: Parameters<NonNullable<UploadProps['customRequest']>>[0]) => {
    try {
      await uploadVideo.mutateAsync({ file: options.file as File, productId: uploadProductId })
      message.success('视频上传成功')
      options.onSuccess?.({})
      actionRef.current?.reload()
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
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '扫描导入失败')
    }
  }, [scanVideos])

  const columns: ProColumns<VideoResponse>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 70,
      sorter: true,
      hideInSearch: true,
    },
    {
      title: '名称',
      dataIndex: 'name',
      ellipsis: true,
      render: (_, record) => (
        <Typography.Link onClick={() => navigate(`/material/video/${record.id}`)}>
          {record.name}
        </Typography.Link>
      ),
    },
    {
      title: '状态',
      dataIndex: 'file_exists',
      width: 70,
      valueEnum: {
        true: { text: '正常', status: 'Success' },
        false: { text: '缺失', status: 'Error' },
      },
      render: (_, record) =>
        record.file_exists === false
          ? <Tag color="error">缺失</Tag>
          : <Tag color="success">正常</Tag>,
    },
    {
      title: '关联商品',
      dataIndex: 'product_id',
      width: 120,
      hideInSearch: true,
      render: (_, record) =>
        record.product_id != null
          ? (
            <Tag
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/material/product/${record.product_id}`)}
            >
              {record.product_id}
            </Tag>
          )
          : <Text type="secondary">—</Text>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      width: 90,
      sorter: true,
      hideInSearch: true,
      render: (_, record) => formatSize(record.file_size ?? null),
    },
    {
      title: '时长',
      dataIndex: 'duration',
      width: 80,
      sorter: true,
      hideInSearch: true,
      render: (_, record) => formatDuration(record.duration ?? null),
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
          <Button
            type="link"
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => setPlayingVideo(record)}
          >
            播放
          </Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small">删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <PageHeader
        title="\u89c6\u9891\u7ba1\u7406"
        subtitle="\u5c06\u9996\u5c4f\u4f5c\u4e3a\u89c6\u9891\u8d44\u4ea7\u7684\u68c0\u7d22\u3001\u4e0a\u4f20\u3001\u6821\u9a8c\u4e0e\u64ad\u653e\u9884\u89c8\u5165\u53e3\uff0c\u4fdd\u6301\u5546\u54c1\u5173\u8054\u4e0e\u6279\u91cf\u64cd\u4f5c\u5728\u540c\u4e00\u5957\u5de5\u4f5c\u6d41\u4e2d\u5b8c\u6210\u3002"
        extra={(
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
            {'\u624b\u52a8\u6dfb\u52a0'}
          </Button>
        )}
      />
      <InlineNotice
        message="\u5148\u9009\u62e9\u5173\u8054\u5546\u54c1\u518d\u4e0a\u4f20\uff0c\u53ef\u4ee5\u51cf\u5c11\u540e\u7eed\u8865\u5173\u8054\u548c\u6574\u7406\u6210\u672c"
        description="\u626b\u63cf\u5bfc\u5165\u9002\u5408\u6279\u91cf\u5165\u5e93\uff0c\u624b\u52a8\u6dfb\u52a0\u9002\u5408\u8865\u5f55\u6587\u4ef6\u8def\u5f84\uff1b\u5217\u8868\u533a\u57df\u53ea\u8d1f\u8d23\u7b5b\u9009\u3001\u72b6\u6001\u5b9a\u4f4d\u548c\u64ad\u653e\u9884\u89c8\u3002"
      />
      <ProTable<VideoResponse>
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        headerTitle={false}
        request={async (params) => {
          const response = await listVideosApiVideosGet({
            query: params.name ? { keyword: params.name as string } : undefined,
          })
          const data = response.data as VideoListResponse
          const fileExists = params.file_exists as string | undefined
          const items = fileExists === undefined
            ? data.items
            : data.items.filter((v) =>
                fileExists === 'true' ? v.file_exists === true : v.file_exists === false
              )
          return { data: items, success: true, total: items.length }
        }}
        rowSelection={{
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        }}
        tableAlertOptionRender={() => (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger size="small" icon={<DeleteOutlined />} loading={batchDeleteVideos.isPending}>
              批量删除 ({selectedIds.length})
            </Button>
          </Popconfirm>
        )}
        toolBarRender={() => [
          <ProductSelect
            key="product-select"
            allowClear
            placeholder="上传到商品"
            style={{ width: 160 }}
            value={uploadProductId}
            onChange={(v) => setUploadProductId(v as number | undefined)}
          />,
          <Upload
            key="upload"
            accept="video/mp4,video/quicktime"
            showUploadList={false}
            customRequest={handleUpload}
          >
            <Button icon={<UploadOutlined />} loading={uploadVideo.isPending}>
              上传视频
            </Button>
          </Upload>,
          <Button key="scan" icon={<ScanOutlined />} onClick={handleScan} loading={scanVideos.isPending}>
            扫描导入
          </Button>,
        ]}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        search={{ labelWidth: 'auto' }}
      />

      <Modal
        title={playingVideo?.name ?? '播放视频'}
        open={playingVideo !== null}
        onCancel={() => setPlayingVideo(null)}
        footer={null}
        destroyOnHidden
        width={720}
      >
        {playingVideo && (
          <video
            controls
            src={`${API_BASE}/videos/${playingVideo.id}/stream`}
            style={{ width: '100%' }}
          />
        )}
      </Modal>

      <Modal
        title="添加视频"
        open={addModalOpen}
        onOk={handleAdd}
        confirmLoading={createVideo.isPending}
        onCancel={() => { setAddModalOpen(false); form.resetFields() }}
        destroyOnHidden
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
    </Space>
  )
}
