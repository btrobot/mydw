import { useCallback, useRef } from 'react'
import {
  Button, message, Popconfirm, Upload,
} from 'antd'
import type { UploadProps } from 'antd'
import { UploadOutlined, DeleteOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'
import { useState } from 'react'

import { useUploadAudio, useDeleteAudio, useBatchDeleteAudios } from '@/hooks'
import type { AudioResponse } from '@/types/material'
import { formatSize, formatDuration } from '@/utils/format'
import { handleApiError } from '@/utils/error'
import { api } from '@/services/api'

export default function AudioList() {
  const actionRef = useRef<ActionType>()
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  const uploadAudio = useUploadAudio()
  const deleteAudio = useDeleteAudio()
  const batchDeleteAudios = useBatchDeleteAudios()

  const handleUpload = useCallback(async (options: Parameters<NonNullable<UploadProps['customRequest']>>[0]) => {
    try {
      await uploadAudio.mutateAsync(options.file as File)
      message.success('音频上传成功')
      options.onSuccess?.({})
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '音频上传失败')
      options.onError?.(new Error('上传失败') as never)
    }
  }, [uploadAudio])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteAudio.mutateAsync(id)
      message.success('删除成功')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除音频失败')
    }
  }, [deleteAudio])

  const handleBatchDelete = useCallback(async () => {
    try {
      const result = await batchDeleteAudios.mutateAsync(selectedIds)
      setSelectedIds([])
      message.success(`已删除 ${result.deleted} 个音频${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, batchDeleteAudios])

  const columns: ProColumns<AudioResponse>[] = [
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
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      width: 90,
      sorter: true,
      hideInSearch: true,
      render: (_, record) => formatSize(record.file_size),
    },
    {
      title: '时长',
      dataIndex: 'duration',
      width: 80,
      sorter: true,
      hideInSearch: true,
      render: (_, record) => formatDuration(record.duration),
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
          <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <ProTable<AudioResponse>
      actionRef={actionRef}
      rowKey="id"
      columns={columns}
      request={async (params) => {
        const { data } = await api.get<AudioResponse[]>('/audios', {
          params: params.name ? { keyword: params.name } : undefined,
        })
        return { data, success: true, total: data.length }
      }}
      rowSelection={{
        selectedRowKeys: selectedIds,
        onChange: (keys) => setSelectedIds(keys as number[]),
      }}
      tableAlertOptionRender={() => (
        <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
          <Button danger size="small" icon={<DeleteOutlined />} loading={batchDeleteAudios.isPending}>
            批量删除 ({selectedIds.length})
          </Button>
        </Popconfirm>
      )}
      toolBarRender={() => [
        <Upload
          key="upload"
          accept="audio/mpeg,audio/mp3,audio/wav,audio/aac,audio/ogg"
          showUploadList={false}
          customRequest={handleUpload}
        >
          <Button icon={<UploadOutlined />} loading={uploadAudio.isPending}>
            上传音频
          </Button>
        </Upload>,
      ]}
      pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
      size="small"
      search={{ labelWidth: 'auto' }}
    />
  )
}
