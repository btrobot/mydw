import { useState, useCallback } from 'react'
import {
  Table, Button, Space, Typography, message,
  Popconfirm, Upload, Tag,
} from 'antd'
import type { UploadProps } from 'antd'
import { DeleteOutlined, UploadOutlined } from '@ant-design/icons'

import { useCovers, useUploadCover, useDeleteCover, useBatchDeleteCovers } from '@/hooks'
import type { CoverResponse } from '@/types/material'
import { formatSize } from '@/utils/format'
import { handleApiError } from '@/utils/error'

const { Text } = Typography

export default function CoverList() {
  const [videoFilter, setVideoFilter] = useState<number | undefined>(undefined)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const { data: covers = [], isLoading } = useCovers(videoFilter)
  const uploadCover = useUploadCover()
  const deleteCover = useDeleteCover()
  const batchDeleteCovers = useBatchDeleteCovers()

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
        <input
          type="number"
          placeholder="视频ID筛选"
          style={{ width: 140, padding: '4px 8px', border: '1px solid #d9d9d9', borderRadius: 6 }}
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
