import { useQuery } from '@tanstack/react-query'
import { Row, Col, Card, Statistic, Button, Space, Typography } from 'antd'
import {
  VideoCameraOutlined, FileTextOutlined, PictureOutlined,
  SoundOutlined, TagsOutlined, ShopOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '@/services/api'

const { Title } = Typography

interface MaterialStats {
  videos: number
  copywritings: number
  covers: number
  audios: number
  topics: number
  coverage_rate: number
}

export default function MaterialOverview() {
  const navigate = useNavigate()
  const { data: stats } = useQuery<MaterialStats>({
    queryKey: ['material-stats'],
    queryFn: async () => (await api.get('/system/material-stats')).data,
  })

  return (
    <>
      <Title level={4} style={{ marginTop: 0, marginBottom: 16 }}>素材总览</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic title="视频" value={stats?.videos ?? 0} prefix={<VideoCameraOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="文案" value={stats?.copywritings ?? 0} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="封面" value={stats?.covers ?? 0} prefix={<PictureOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="音频" value={stats?.audios ?? 0} prefix={<SoundOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="话题" value={stats?.topics ?? 0} prefix={<TagsOutlined />} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic
              title="商品覆盖率"
              value={(stats?.coverage_rate ?? 0) * 100}
              suffix="%"
              precision={0}
              prefix={<ShopOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="快捷操作" size="small">
        <Space wrap>
          <Button onClick={() => navigate('/material/video')}>视频管理</Button>
          <Button onClick={() => navigate('/material/copywriting')}>文案管理</Button>
          <Button onClick={() => navigate('/material/cover')}>封面管理</Button>
          <Button onClick={() => navigate('/material/audio')}>音频管理</Button>
          <Button onClick={() => navigate('/material/topic')}>话题管理</Button>
          <Button onClick={() => navigate('/product')}>商品管理</Button>
        </Space>
      </Card>
    </>
  )
}
