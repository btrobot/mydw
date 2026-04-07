import { useState, useCallback } from 'react'
import {
  Table, Button, Space, message,
  Popconfirm, Upload,
} from 'antd'
import type { UploadProps } from 'antd'
import { DeleteOutlined, UploadOutlined } from '@ant-design/icons'

import { useAudios, useUploadAudio, useDeleteAudio, useBatchDeleteAudios } from '@/hooks'
import type { AudioResponse } from '@/types/material'
import { formatSize, formatDuration } from '@/utils/format'
import { handleApiError } from '@/utils/error'

export default function AudioList() {
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const { data: audios = [], isLoading } = useAudios()
  const uploadAudio = useUploadAudio()
  const deleteAudio = useDeleteAudio()
  const batchDeleteAudios = useBatchDeleteAudios()

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
