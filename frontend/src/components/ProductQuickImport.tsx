import { useState } from 'react'
import { Select, Button, Space, message, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useProducts, useProductMaterials } from '@/hooks/useProduct'
import type { VideoResponse, CopywritingResponse, CoverResponse, AudioResponse } from '@/types/material'

const { Text } = Typography

interface ProductQuickImportProps {
  onImport: (materials: {
    videos?: VideoResponse[]
    copywritings?: CopywritingResponse[]
    covers?: CoverResponse[]
    audios?: AudioResponse[]
  }) => void
}

export default function ProductQuickImport({ onImport }: ProductQuickImportProps) {
  const [selectedProductId, setSelectedProductId] = useState<number | undefined>(undefined)
  const { data: products = [] } = useProducts()
  const { data: materials, isLoading } = useProductMaterials(selectedProductId)

  const handleImport = () => {
    if (!materials || !selectedProductId) {
      message.warning('请先选择商品')
      return
    }

    // Guard against stale data
    if (materials.product.id !== selectedProductId) {
      message.warning('素材加载中，请稍候')
      return
    }

    const count = materials.videos.length + materials.copywritings.length + materials.covers.length
    if (count === 0) {
      message.warning('该商品没有可用素材')
      return
    }

    onImport({
      videos: materials.videos,
      copywritings: materials.copywritings,
      covers: materials.covers,
    })

    message.success(`已添加 ${count} 项素材到素材篮`)
    setSelectedProductId(undefined)
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Text strong>商品快速导入</Text>
      <Text type="secondary" style={{ fontSize: 12 }}>
        选择商品后，一键导入该商品的所有素材
      </Text>
      <Space.Compact style={{ width: '100%' }}>
        <Select
          style={{ flex: 1 }}
          placeholder="选择商品"
          value={selectedProductId}
          onChange={setSelectedProductId}
          showSearch
          optionFilterProp="label"
          options={products.map((p) => ({
            value: p.id,
            label: p.name,
          }))}
        />
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleImport}
          loading={isLoading}
          disabled={!selectedProductId || isLoading || !materials}
        >
          添加到素材篮
        </Button>
      </Space.Compact>
    </Space>
  )
}
