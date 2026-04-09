import { List, Empty, Space, Button, Typography, Divider } from 'antd'
import { DeleteOutlined, VideoCameraOutlined, FileTextOutlined, PictureOutlined, AudioOutlined } from '@ant-design/icons'
import type { VideoResponse, CopywritingResponse, CoverResponse, AudioResponse } from '@/types/material'

const { Text } = Typography

interface MaterialBasketProps {
  basket: {
    videos: VideoResponse[]
    copywritings: CopywritingResponse[]
    covers: CoverResponse[]
    audios: AudioResponse[]
  }
  onRemove: (type: 'videos' | 'copywritings' | 'covers' | 'audios', id: number) => void
}

export default function MaterialBasket({ basket, onRemove }: MaterialBasketProps) {
  const isEmpty = basket.videos.length === 0 && basket.copywritings.length === 0 && basket.covers.length === 0 && basket.audios.length === 0

  if (isEmpty) {
    return (
      <Empty
        description="素材篮为空"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ padding: '40px 0' }}
      >
        <Text type="secondary">从左侧添加素材到素材篮</Text>
      </Empty>
    )
  }

  return (
    <div>
      {basket.videos.length > 0 && (
        <>
          <Space style={{ marginBottom: 8 }}>
            <VideoCameraOutlined />
            <Text strong>视频 ({basket.videos.length})</Text>
          </Space>
          <List
            size="small"
            dataSource={basket.videos}
            renderItem={(video) => (
              <List.Item
                actions={[
                  <Button
                    key="delete"
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => onRemove('videos', video.id)}
                  />,
                ]}
              >
                <Text ellipsis style={{ maxWidth: 300 }}>{video.name}</Text>
              </List.Item>
            )}
            style={{ marginBottom: 16 }}
          />
        </>
      )}

      {basket.copywritings.length > 0 && (
        <>
          <Space style={{ marginBottom: 8 }}>
            <FileTextOutlined />
            <Text strong>文案 ({basket.copywritings.length})</Text>
          </Space>
          <List
            size="small"
            dataSource={basket.copywritings}
            renderItem={(copywriting) => (
              <List.Item
                actions={[
                  <Button
                    key="delete"
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => onRemove('copywritings', copywriting.id)}
                  />,
                ]}
              >
                <Text ellipsis style={{ maxWidth: 300 }}>{copywriting.name}</Text>
              </List.Item>
            )}
            style={{ marginBottom: 16 }}
          />
        </>
      )}

      {basket.covers.length > 0 && (
        <>
          <Space style={{ marginBottom: 8 }}>
            <PictureOutlined />
            <Text strong>封面 ({basket.covers.length})</Text>
          </Space>
          <List
            size="small"
            dataSource={basket.covers}
            renderItem={(cover) => (
              <List.Item
                actions={[
                  <Button
                    key="delete"
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => onRemove('covers', cover.id)}
                  />,
                ]}
              >
                <Text ellipsis style={{ maxWidth: 300 }}>
                  {cover.name || cover.file_path.split(/[/\\]/).pop() || `封面 #${cover.id}`}
                </Text>
              </List.Item>
            )}
            style={{ marginBottom: 16 }}
          />
        </>
      )}

      {basket.audios.length > 0 && (
        <>
          <Space style={{ marginBottom: 8 }}>
            <AudioOutlined />
            <Text strong>音频 ({basket.audios.length})</Text>
          </Space>
          <List
            size="small"
            dataSource={basket.audios}
            renderItem={(audio) => (
              <List.Item
                actions={[
                  <Button
                    key="delete"
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => onRemove('audios', audio.id)}
                  />,
                ]}
              >
                <Text ellipsis style={{ maxWidth: 300 }}>{audio.name}</Text>
              </List.Item>
            )}
          />
        </>
      )}

      <Divider style={{ margin: '16px 0' }} />
      <Text type="secondary">
        共 {basket.videos.length + basket.copywritings.length + basket.covers.length + basket.audios.length} 项素材
      </Text>
    </div>
  )
}
