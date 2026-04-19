import { useState, useMemo } from 'react'
import { Modal, Table, Input, Space, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useVideos } from '@/hooks/useVideo'
import { useCopywritings } from '@/hooks/useCopywriting'
import { useCovers } from '@/hooks/useCover'
import { useAudios } from '@/hooks/useAudio'
import type { VideoResponse, CopywritingResponse, CoverResponse, AudioResponse } from '@/types/material'
import type { TableRowSelection } from 'antd/es/table/interface'

type MaterialType = 'video' | 'copywriting' | 'cover' | 'audio'

interface MaterialSelectModalProps {
  visible: boolean
  materialType: MaterialType
  onConfirm: (materials: VideoResponse[] | CopywritingResponse[] | CoverResponse[] | AudioResponse[]) => void
  onCancel: () => void
}

const MATERIAL_LABELS: Record<MaterialType, string> = {
  video: '视频',
  copywriting: '文案',
  cover: '封面',
  audio: '音频',
}

export default function MaterialSelectModal({ visible, materialType, onConfirm, onCancel }: MaterialSelectModalProps) {
  const [keyword, setKeyword] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])

  const { data: videos = [], isLoading: videosLoading, error: videosError } = useVideos({ keyword })
  const { data: copywritings = [], isLoading: copywritingsLoading, error: copywritingsError } = useCopywritings({ keyword })
  const { data: covers = [], isLoading: coversLoading, error: coversError } = useCovers()
  const { data: audios = [], isLoading: audiosLoading, error: audiosError } = useAudios(keyword)

  const dataSource = useMemo(() => {
    switch (materialType) {
      case 'video':
        return videos
      case 'copywriting':
        return copywritings
      case 'cover':
        return covers
      case 'audio':
        return audios
      default:
        return []
    }
  }, [materialType, videos, copywritings, covers, audios])

  const loading = useMemo(() => {
    switch (materialType) {
      case 'video':
        return videosLoading
      case 'copywriting':
        return copywritingsLoading
      case 'cover':
        return coversLoading
      case 'audio':
        return audiosLoading
      default:
        return false
    }
  }, [materialType, videosLoading, copywritingsLoading, coversLoading, audiosLoading])

  const queryError = useMemo(() => {
    switch (materialType) {
      case 'video':
        return videosError
      case 'copywriting':
        return copywritingsError
      case 'cover':
        return coversError
      case 'audio':
        return audiosError
      default:
        return null
    }
  }, [audiosError, copywritingsError, coversError, materialType, videosError])

  const emptyText = queryError instanceof Error
    ? `素材加载失败：${queryError.message}`
    : '暂无可选素材'

  const columns = useMemo(() => {
    const baseColumns = [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
        ellipsis: true,
      },
    ]

    if (materialType === 'video') {
      return [
        ...baseColumns,
        {
          title: '时长',
          dataIndex: 'duration',
          key: 'duration',
          width: 100,
          render: (duration: number | null) => duration ? `${duration.toFixed(1)}s` : '-',
        },
        {
          title: '来源商品',
          dataIndex: 'product_name',
          key: 'product_name',
          width: 150,
          ellipsis: true,
          render: (name: string | null) => name || '-',
        },
      ]
    }

    if (materialType === 'copywriting') {
      return [
        ...baseColumns,
        {
          title: '内容预览',
          dataIndex: 'content',
          key: 'content',
          ellipsis: true,
          render: (content: string) => content.slice(0, 50) + (content.length > 50 ? '...' : ''),
        },
        {
          title: '来源商品',
          dataIndex: 'product_name',
          key: 'product_name',
          width: 150,
          ellipsis: true,
          render: (name: string | null) => name || '-',
        },
      ]
    }

    if (materialType === 'audio') {
      return [
        ...baseColumns,
        {
          title: '时长',
          dataIndex: 'duration',
          key: 'duration',
          width: 100,
          render: (duration: number | null) => duration ? `${duration.toFixed(1)}s` : '-',
        },
      ]
    }

    return baseColumns
  }, [materialType])

  const rowSelection: TableRowSelection<VideoResponse | CopywritingResponse | CoverResponse | AudioResponse> = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys as number[]),
  }

  const handleOk = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请至少选择一项素材')
      return
    }

    const selectedMaterials = dataSource.filter((item) => selectedRowKeys.includes(item.id))
    onConfirm(selectedMaterials as VideoResponse[] | CopywritingResponse[] | CoverResponse[] | AudioResponse[])
    setSelectedRowKeys([])
    setKeyword('')
  }

  const handleCancel = () => {
    setSelectedRowKeys([])
    setKeyword('')
    onCancel()
  }

  return (
    <Modal
      title={`选择${MATERIAL_LABELS[materialType]}`}
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      width={800}
      okText="确定"
      cancelText="取消"
      destroyOnClose
    >
      <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
        <Input
          placeholder={`搜索${MATERIAL_LABELS[materialType]}`}
          prefix={<SearchOutlined />}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          allowClear
        />
      </Space>

      <Table
        rowKey="id"
        dataSource={dataSource}
        columns={columns}
        rowSelection={rowSelection}
        loading={loading}
        locale={{ emptyText }}
        pagination={{ pageSize: 10, showSizeChanger: false }}
        size="small"
      />
    </Modal>
  )
}
