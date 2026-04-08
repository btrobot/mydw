import { useParams, useNavigate } from 'react-router-dom'
import { Flex, Spin, Typography } from 'antd'
import { PageContainer, ProDescriptions } from '@ant-design/pro-components'

import { useVideo } from '@/hooks'
import { formatSize, formatDuration } from '@/utils/format'

const { Text } = Typography

export default function VideoDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const videoId = id ? parseInt(id, 10) : undefined

  const { data: video, isLoading } = useVideo(videoId)

  if (isLoading) {
    return (
      <Flex justify="center" style={{ padding: 48 }}>
        <Spin size="large" />
      </Flex>
    )
  }

  if (!video) {
    return (
      <PageContainer title="视频不存在" onBack={() => navigate(-1)}>
        <Text type="secondary">视频不存在或已被删除</Text>
      </PageContainer>
    )
  }

  return (
    <PageContainer title={video.name} onBack={() => navigate(-1)}>
      <video
        controls
        src={`http://127.0.0.1:8000/api/videos/${videoId}/stream`}
        style={{ width: '100%', maxHeight: 500, display: 'block', marginBottom: 24 }}
      />

      <ProDescriptions<typeof video>
        dataSource={video}
        bordered
        size="small"
        column={2}
        columns={[
          { title: '视频名称', dataIndex: 'name' },
          {
            title: '文件大小',
            dataIndex: 'file_size',
            render: (_, r) => formatSize(r.file_size),
          },
          {
            title: '时长',
            dataIndex: 'duration',
            render: (_, r) => formatDuration(r.duration),
          },
          {
            title: '关联商品',
            dataIndex: 'product_id',
            render: (_, r) =>
              r.product_id ? (
                <a onClick={() => navigate(`/material/product/${r.product_id}`)}>
                  {r.product_name ?? String(r.product_id)}
                </a>
              ) : (
                <Text type="secondary">—</Text>
              ),
          },
          {
            title: '创建时间',
            dataIndex: 'created_at',
            render: (_, r) => new Date(r.created_at).toLocaleString('zh-CN'),
          },
        ]}
      />
    </PageContainer>
  )
}
