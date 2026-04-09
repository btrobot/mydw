import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card, Form, Select, Button, Space, message, Typography,
} from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useAccounts, useAssembleTasks } from '@/hooks'
import { useVideos } from '@/hooks/useVideo'
import { useCovers } from '@/hooks/useCover'
import { useProfiles } from '@/hooks/useProfile'
import type { PublishProfileResponse } from '@/hooks/useProfile'
import type { AccountResponseExtended } from '@/hooks/useAccount'
import type { VideoResponse } from '@/types/material'

const { Text, Title } = Typography

interface AssembleFormValues {
  video_ids: number[]
  account_ids: number[]
  strategy: string
  copywriting_mode: string
  cover_id?: number | null
  profile_id?: number | null
}

const COMPOSITION_MODE_LABEL: Record<string, string> = {
  none: '无需合成',
  coze: 'Coze 合成',
  local_ffmpeg: '本地 FFmpeg 合成',
}

export default function TaskAssemble() {
  const navigate = useNavigate()
  const [form] = Form.useForm<AssembleFormValues>()
  const [selectedCompositionMode, setSelectedCompositionMode] = useState<string | null>(null)

  const { data: accounts = [] } = useAccounts()
  const { data: videos = [] } = useVideos()
  const { data: covers = [] } = useCovers()
  const { data: profilesData } = useProfiles()
  const assembleTasks = useAssembleTasks()

  const profiles = profilesData?.items ?? []

  // Set default profile on mount
  const defaultProfile = profiles.find((p: PublishProfileResponse) => p.is_default)

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields()
      const result = await assembleTasks.mutateAsync(values)
      const count = Array.isArray(result) ? result.length : 0
      message.success(`组装成功，共生成 ${count} 个任务`)
      navigate('/task/list')
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('组装失败')
      }
    }
  }, [form, assembleTasks, navigate])

  return (
    <div style={{ maxWidth: 640 }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/task/list')}>返回</Button>
        <Title level={4} style={{ margin: 0 }}>组装任务</Title>
      </Space>

      <Card>
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
            name="video_ids"
            label="选择视频"
            rules={[{ required: true, message: '请选择至少一个视频' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择视频"
              optionFilterProp="label"
              options={videos.map((v: VideoResponse) => ({ value: v.id, label: v.name }))}
            />
          </Form.Item>
          <Form.Item
            name="account_ids"
            label="选择账号"
            rules={[{ required: true, message: '请选择至少一个账号' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择账号"
              optionFilterProp="label"
              options={accounts.map((a: AccountResponseExtended) => ({ value: a.id, label: a.account_name }))}
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
                { value: 'manual', label: '手动指定' },
              ]}
            />
          </Form.Item>
          <Form.Item name="cover_id" label="封面（可选）">
            <Select
              allowClear
              placeholder="选择封面"
              options={covers.map((c) => ({ value: c.id, label: c.file_path.split(/[/\\]/).pop() ?? `封面 #${c.id}` }))}
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
              <Button type="primary" onClick={handleSubmit} loading={assembleTasks.isPending}>
                开始组装
              </Button>
              <Button onClick={() => navigate('/task/list')}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
