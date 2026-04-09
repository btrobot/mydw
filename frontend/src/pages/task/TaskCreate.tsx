import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card, Form, Select, Button, Space, message, Typography, Row, Col, List, Tag, Empty, Divider,
} from 'antd'
import { ArrowLeftOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { useAccounts } from '@/hooks/useAccount'
import { useProfiles } from '@/hooks/useProfile'
import { useBatchAssemble } from '@/hooks/useTask'
import { useProducts } from '@/hooks/useProduct'
import type { PublishProfileResponse } from '@/hooks/useProfile'
import type { AccountResponseExtended } from '@/hooks/useAccount'
import type { VideoResponse, CopywritingResponse, CoverResponse, AudioResponse } from '@/types/material'
import MaterialBasket from '@/components/MaterialBasket'
import ProductQuickImport from '@/components/ProductQuickImport'

const { Text, Title } = Typography

interface TaskCreateFormValues {
  account_ids: number[]
  strategy: 'round_robin' | 'manual'
  copywriting_mode: 'auto_match' | 'round_robin'
  profile_id?: number | null
}

interface MaterialBasketState {
  videos: VideoResponse[]
  copywritings: CopywritingResponse[]
  covers: CoverResponse[]
  audios: AudioResponse[]
}

const COMPOSITION_MODE_LABEL: Record<string, string> = {
  none: '无需合成',
  coze: 'Coze 合成',
  local_ffmpeg: '本地 FFmpeg 合成',
}

export default function TaskCreate() {
  const navigate = useNavigate()
  const [form] = Form.useForm<TaskCreateFormValues>()
  const [basket, setBasket] = useState<MaterialBasketState>({
    videos: [],
    copywritings: [],
    covers: [],
    audios: [],
  })
  const [selectedCompositionMode, setSelectedCompositionMode] = useState<string | null>(null)

  const { data: accounts = [] } = useAccounts()
  const { data: profilesData } = useProfiles()
  const batchAssemble = useBatchAssemble()

  const profiles = profilesData?.items ?? []
  const defaultProfile = profiles.find((p: PublishProfileResponse) => p.is_default)

  const addToBasket = useCallback((materials: Partial<MaterialBasketState>) => {
    setBasket((prev) => {
      const newBasket = { ...prev }

      if (materials.videos) {
        const existingIds = new Set(prev.videos.map((v) => v.id))
        const newVideos = materials.videos.filter((v) => !existingIds.has(v.id))
        newBasket.videos = [...prev.videos, ...newVideos]
      }

      if (materials.copywritings) {
        const existingIds = new Set(prev.copywritings.map((c) => c.id))
        const newCopywritings = materials.copywritings.filter((c) => !existingIds.has(c.id))
        newBasket.copywritings = [...prev.copywritings, ...newCopywritings]
      }

      if (materials.covers) {
        const existingIds = new Set(prev.covers.map((c) => c.id))
        const newCovers = materials.covers.filter((c) => !existingIds.has(c.id))
        newBasket.covers = [...prev.covers, ...newCovers]
      }

      if (materials.audios) {
        const existingIds = new Set(prev.audios.map((a) => a.id))
        const newAudios = materials.audios.filter((a) => !existingIds.has(a.id))
        newBasket.audios = [...prev.audios, ...newAudios]
      }

      return newBasket
    })
  }, [])

  const removeFromBasket = useCallback((type: keyof MaterialBasketState, id: number) => {
    setBasket((prev) => ({
      ...prev,
      [type]: prev[type].filter((item) => item.id !== id),
    }))
  }, [])

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields()

      if (basket.videos.length === 0) {
        message.warning('请至少添加一个视频')
        return
      }

      if (values.account_ids.length === 0) {
        message.warning('请至少选择一个账号')
        return
      }

      const result = await batchAssemble.mutateAsync({
        video_ids: basket.videos.map((v) => v.id),
        copywriting_ids: basket.copywritings.map((c) => c.id),
        cover_ids: basket.covers.map((c) => c.id),
        audio_ids: basket.audios.map((a) => a.id),
        account_ids: values.account_ids,
        strategy: values.strategy,
        copywriting_mode: values.copywriting_mode,
        profile_id: values.profile_id,
      })

      const count = Array.isArray(result) ? result.length : 0
      message.success(`创建成功，共生成 ${count} 个任务`)
      navigate('/task/list')
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('创建失败')
      }
    }
  }, [form, basket, batchAssemble, navigate])

  const basketCount = basket.videos.length + basket.copywritings.length + basket.covers.length + basket.audios.length

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/task/list')}>返回</Button>
        <Title level={4} style={{ margin: 0 }}>创建任务</Title>
      </Space>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="素材来源" style={{ marginBottom: 16 }}>
            <ProductQuickImport onImport={addToBasket} />
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title={
              <Space>
                <span>素材篮</span>
                {basketCount > 0 && <Tag color="blue">{basketCount} 项</Tag>}
              </Space>
            }
          >
            <MaterialBasket basket={basket} onRemove={removeFromBasket} />
          </Card>
        </Col>
      </Row>

      <Card title="发布配置">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            strategy: 'round_robin',
            copywriting_mode: 'auto_match',
            profile_id: defaultProfile?.id,
          }}
        >
          <Form.Item
            name="account_ids"
            label="选择账号"
            rules={[{ required: true, message: '请选择至少一个账号' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择账号"
              optionFilterProp="label"
              options={accounts.map((a: AccountResponseExtended) => ({
                value: a.id,
                label: a.account_name,
              }))}
            />
          </Form.Item>

          <Form.Item name="strategy" label="分配策略">
            <Select
              options={[
                { value: 'round_robin', label: '轮询分配' },
                { value: 'manual', label: '手动分配' },
              ]}
            />
          </Form.Item>

          <Form.Item name="copywriting_mode" label="文案模式">
            <Select
              options={[
                { value: 'auto_match', label: '自动匹配' },
                { value: 'round_robin', label: '轮询分配' },
              ]}
            />
          </Form.Item>

          <Form.Item name="profile_id" label="发布配置档（可选）">
            <Select
              allowClear
              placeholder="选择配置档（不选则使用默认）"
              optionFilterProp="label"
              onChange={(value: number | null | undefined) => {
                const profile = profiles.find((p: PublishProfileResponse) => p.id === value)
                setSelectedCompositionMode(profile?.composition_mode ?? null)
              }}
              options={profiles.map((p: PublishProfileResponse) => ({
                value: p.id,
                label: p.is_default ? `${p.name}（默认）` : p.name,
              }))}
            />
          </Form.Item>

          {selectedCompositionMode !== null && (
            <Form.Item>
              <Text type="secondary">
                合成方式：{COMPOSITION_MODE_LABEL[selectedCompositionMode] ?? selectedCompositionMode}
              </Text>
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button
                type="primary"
                onClick={handleSubmit}
                loading={batchAssemble.isPending}
                disabled={basket.videos.length === 0}
              >
                创建任务
              </Button>
              <Button onClick={() => navigate('/task/list')}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
