import type { JSX } from 'react'

import {
  FileTextOutlined,
  PictureOutlined,
  ReloadOutlined,
  ShopOutlined,
  SoundOutlined,
  TagsOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Button, Card, Col, Row, Space, Statistic } from 'antd'
import { useNavigate } from 'react-router-dom'

import { materialStatsApiSystemMaterialStatsGet } from '@/api'
import type { MaterialStatsResponse } from '@/api'
import { InlineNotice } from '@/components/feedback/InlineNotice'
import { PageError } from '@/components/feedback/PageError'
import { PageLoading } from '@/components/feedback/PageLoading'
import { PageHeader } from '@/components/ui/PageHeader'

type MaterialCardItem = {
  key: string
  title: string
  actionLabel: string
  path: string
  value: number
  icon: JSX.Element
  precision?: number
  suffix?: string
}

export default function MaterialOverview() {
  const navigate = useNavigate()
  const materialStatsQuery = useQuery<MaterialStatsResponse>({
    queryKey: ['material-stats'],
    queryFn: async () => {
      const response = await materialStatsApiSystemMaterialStatsGet({ throwOnError: true })
      return response.data!
    },
  })

  const stats = materialStatsQuery.data
  const materialCards: MaterialCardItem[] = [
    { key: 'video', title: '视频', actionLabel: '视频管理', path: '/material/video', value: stats?.videos ?? 0, icon: <VideoCameraOutlined /> },
    { key: 'copywriting', title: '文案', actionLabel: '文案管理', path: '/material/copywriting', value: stats?.copywritings ?? 0, icon: <FileTextOutlined /> },
    { key: 'cover', title: '封面', actionLabel: '封面管理', path: '/material/cover', value: stats?.covers ?? 0, icon: <PictureOutlined /> },
    { key: 'audio', title: '音频', actionLabel: '音频管理', path: '/material/audio', value: stats?.audios ?? 0, icon: <SoundOutlined /> },
    { key: 'topic', title: '话题', actionLabel: '话题管理', path: '/material/topic', value: stats?.topics ?? 0, icon: <TagsOutlined /> },
    { key: 'product', title: '商品覆盖率', actionLabel: '商品管理', path: '/material/product', value: (stats?.coverage_rate ?? 0) * 100, icon: <ShopOutlined />, precision: 0, suffix: '%' },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <PageHeader
        title="素材管理"
        subtitle="将首屏作为素材资产概览与快捷分流入口，让视频、文案、封面等类型能在同一套布局中被快速扫视。"
      />
      <InlineNotice
        message="先看总量和覆盖率，再进入单类素材页面处理具体内容"
        description="这个概览首屏只承担资产分布与快速跳转，避免把导航、统计和具体编辑混在一起。"
      />

      {materialStatsQuery.isLoading && !stats ? (
        <PageLoading
          title="正在加载素材概览"
          description="稍后即可查看各类素材的总量与商品覆盖情况。"
          testId="material-overview-loading"
        />
      ) : materialStatsQuery.isError ? (
        <PageError
          title="素材统计暂时不可用"
          description="当前无法获取素材首屏数据，但不会用 0 或占位值掉落为“正常状态”。"
          extra={(
            <Button size="small" icon={<ReloadOutlined />} onClick={() => void materialStatsQuery.refetch()}>
              重试
            </Button>
          )}
          testId="material-overview-error"
        />
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {materialCards.map((item) => (
              <Col key={item.key} xs={24} sm={12} lg={8} xxl={4}>
                <Card size="small" hoverable style={{ cursor: 'pointer' }} onClick={() => navigate(item.path)}>
                  <Statistic
                    title={item.title}
                    value={item.value}
                    prefix={item.icon}
                    precision={item.precision}
                    suffix={item.suffix}
                  />
                </Card>
              </Col>
            ))}
          </Row>

          <Card title="快捷操作" size="small">
            <Space wrap>
              {materialCards.map((item) => (
                <Button key={item.key} onClick={() => navigate(item.path)}>
                  {item.actionLabel}
                </Button>
              ))}
            </Space>
          </Card>
        </>
      )}
    </Space>
  )
}
