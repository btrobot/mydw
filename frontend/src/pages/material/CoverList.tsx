import { useState, useCallback, useRef } from 'react'
import {
  Button, Typography, message,
  Popconfirm, Upload, Image,
} from 'antd'
import type { UploadProps } from 'antd'
import { UploadOutlined, DeleteOutlined, VideoCameraOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'
import { useNavigate } from 'react-router-dom'

import { useUploadCover, useDeleteCover, useBatchDeleteCovers, useVideos } from '@/hooks'
import type { CoverResponse } from '@/types/material'
import { formatSize } from '@/utils/format'
import { handleApiError } from '@/utils/error'
import { api } from '@/services/api'

const { Text } = Typography

export default function CoverList() {
  const actionRef = useRef<ActionType>()
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const navigate = useNavigate()

  const { data: videos = [] } = useVideos()
  const uploadCover = useUploadCover()
  const deleteCover = useDeleteCover()
  const batchDeleteCovers = useBatchDeleteCovers()

  const handleUpload = useCallback(async (options: Parameters<NonNullable<UploadProps['customRequest']>>[0]) => {
    try {
      await uploadCover.mutateAsync({ file: options.file as File })
      message.success('封面上传成功')
      options.onSuccess?.({})
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '封面上传失败')
      options.onError?.(new Error('上传失败') as never)
    }
  }, [uploadCover])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteCover.mutateAsync(id)
      message.success('删除成功')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除封面失败')
    }
  }, [deleteCover])

  const handleBatchDelete = useCallback(async () => {
    try {
      const result = await batchDeleteCovers.mutateAsync(selectedIds)
      setSelectedIds([])
      message.success(`已删除 ${result.deleted} 个封面${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, batchDeleteCovers])

  const columns: ProColumns<CoverResponse>[] = [
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
      hideInSearch: true,
      render: (_, record) => (
        <Image
          width={48}
          height={48}
          src={`http://127.0.0.1:8000/api/covers/${record.id}/image`}
          preview={{ src: `http://127.0.0.1:8000/api/covers/${record.id}/image` }}
          style={{ objectFit: 'cover', cursor: 'pointer' }}
          alt={record.name}
        />
      ),
    },
    {
      title: '关联视频',
      dataIndex: 'video_id',
      width: 120,
      valueType: 'select',
      fieldProps: {
        placeholder: '按视频筛选',
        allowClear: true,
        options: videos.map((v) => ({ label: v.name, value: v.id })),
      },
      render: (_, record) =>
        record.video_id ? (
          <Button
            type="link"
            size="small"
            icon={<VideoCameraOutlined />}
            onClick={() => navigate('/material/video')}
          />
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      width: 90,
      hideInSearch: true,
      render: (_, record) => formatSize(record.file_size),
    },
    {
      title: '尺寸',
      key: 'dimensions',
      width: 100,
      hideInSearch: true,
      render: (_, record) =>
        record.width && record.height ? `${record.width}×${record.height}` : '—',
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
      width: 80,
      hideInSearch: true,
      render: (_, record) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <ProTable<CoverResponse>
      actionRef={actionRef}
      rowKey="id"
      columns={columns}
      request={async (params) => {
        const { data } = await api.get<CoverResponse[]>('/covers', {
          params: params.video_id !== undefined ? { video_id: params.video_id } : undefined,
        })
        return { data, success: true, total: data.length }
      }}
      rowSelection={{
        selectedRowKeys: selectedIds,
        onChange: (keys) => setSelectedIds(keys as number[]),
      }}
      tableAlertOptionRender={() => (
        <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
          <Button danger size="small" icon={<DeleteOutlined />} loading={batchDeleteCovers.isPending}>
            批量删除 ({selectedIds.length})
          </Button>
        </Popconfirm>
      )}
      toolBarRender={() => [
        <Upload
          key="upload"
          accept="image/jpeg,image/png,image/webp"
          showUploadList={false}
          customRequest={handleUpload}
        >
          <Button icon={<UploadOutlined />} loading={uploadCover.isPending} type="primary">
            上传封面
          </Button>
        </Upload>,
      ]}
      pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
      size="small"
      search={{ labelWidth: 'auto' }}
    />
  )
}
