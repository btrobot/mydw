import { useState, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert, App, Card, Form, Select, Button, Space, Typography, Tabs, Table, Popconfirm, Tag, Empty,
} from 'antd'
import { ArrowLeftOutlined, DeleteOutlined, PlusOutlined, VideoCameraOutlined, FileTextOutlined, PictureOutlined, AudioOutlined, ClearOutlined } from '@ant-design/icons'
import { useAccounts } from '@/hooks/useAccount'
import { useProfiles } from '@/hooks/useProfile'
import { useSystemConfig } from '@/hooks/useSystem'
import { useBatchAssemble } from '@/hooks/useTask'
import type { PublishProfileResponse } from '@/hooks/useProfile'
import type { AccountResponseExtended } from '@/hooks/useAccount'
import type { VideoResponse, CopywritingResponse, CoverResponse, AudioResponse } from '@/types/material'
import ProductQuickImport from '@/components/ProductQuickImport'
import MaterialSelectModal from '@/components/MaterialSelectModal'
import type { TableColumnsType } from 'antd'
import {
  getDirectPublishViolations,
  getLocalFfmpegViolations,
  getTaskMaterialCounts,
  resolveCompositionMode,
} from './taskSemantics'
import { creativeFlowModeMeta, resolveCreativeFlowMode } from '@/features/creative/creativeFlow'

const { Text, Title } = Typography

interface TaskCreateFormValues {
  account_id?: number | null
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

type MaterialType = 'video' | 'copywriting' | 'cover' | 'audio'

export default function TaskCreate() {
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [form] = Form.useForm<TaskCreateFormValues>()
  const [basket, setBasket] = useState<MaterialBasketState>({
    videos: [],
    copywritings: [],
    covers: [],
    audios: [],
  })
  const [activeTab, setActiveTab] = useState<string>('video')
  const [modalVisible, setModalVisible] = useState(false)
  const [modalMaterialType, setModalMaterialType] = useState<MaterialType>('video')
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])

  const {
    data: accounts = [],
    isLoading: accountsLoading,
    error: accountsError,
  } = useAccounts({ status: 'active' })
  const { data: profilesData } = useProfiles()
  const systemConfigQuery = useSystemConfig()
  const batchAssemble = useBatchAssemble()

  const profiles = profilesData?.items ?? []
  const creativeFlowMode = resolveCreativeFlowMode(systemConfigQuery.data)
  const creativeFlowMeta = creativeFlowModeMeta[creativeFlowMode]
  const defaultProfile = profiles.find((p: PublishProfileResponse) => p.is_default)
  const selectedProfileId = Form.useWatch('profile_id', form)
  const selectedMode = useMemo(
    () => resolveCompositionMode(selectedProfileId, profiles),
    [selectedProfileId, profiles],
  )
  const basketCounts = useMemo(
    () => getTaskMaterialCounts({
      video_ids: basket.videos.map((item) => item.id),
      copywriting_ids: basket.copywritings.map((item) => item.id),
      cover_ids: basket.covers.map((item) => item.id),
      audio_ids: basket.audios.map((item) => item.id),
      topic_ids: [],
    }),
    [basket],
  )
  const directPublishViolations = useMemo(
    () => (selectedMode === 'none' ? getDirectPublishViolations(basketCounts) : []),
    [basketCounts, selectedMode],
  )
  const localFfmpegViolations = useMemo(
    () => (selectedMode === 'local_ffmpeg' ? getLocalFfmpegViolations(basketCounts) : []),
    [basketCounts, selectedMode],
  )
  const submitDisabled = basket.videos.length === 0
    || directPublishViolations.length > 0
    || localFfmpegViolations.length > 0

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

  const handleOpenModal = useCallback((type: MaterialType) => {
    setModalMaterialType(type)
    setModalVisible(true)
  }, [])

  const handleModalConfirm = useCallback((materials: VideoResponse[] | CopywritingResponse[] | CoverResponse[] | AudioResponse[]) => {
    const typeMap: Record<MaterialType, keyof MaterialBasketState> = {
      video: 'videos',
      copywriting: 'copywritings',
      cover: 'covers',
      audio: 'audios',
    }
    const basketKey = typeMap[modalMaterialType]
    addToBasket({ [basketKey]: materials })
    message.success(`已添加 ${materials.length} 项素材`)
    setModalVisible(false)
  }, [modalMaterialType, addToBasket])

  const handleBatchDelete = useCallback(() => {
    const typeMap: Record<string, keyof MaterialBasketState> = {
      video: 'videos',
      copywriting: 'copywritings',
      cover: 'covers',
      audio: 'audios',
    }
    const basketKey = typeMap[activeTab]
    setBasket((prev) => ({
      ...prev,
      [basketKey]: prev[basketKey].filter((item) => !selectedRowKeys.includes(item.id)),
    }))
    setSelectedRowKeys([])
    message.success('删除成功')
  }, [activeTab, selectedRowKeys])

  const handleClearAll = useCallback(() => {
    const typeMap: Record<string, keyof MaterialBasketState> = {
      video: 'videos',
      copywriting: 'copywritings',
      cover: 'covers',
      audio: 'audios',
    }
    const basketKey = typeMap[activeTab]
    setBasket((prev) => ({
      ...prev,
      [basketKey]: [],
    }))
    setSelectedRowKeys([])
    message.success('已清空')
  }, [activeTab])

  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields()

      if (basket.videos.length === 0) {
        message.warning('请至少添加一个视频')
        return
      }

      if (selectedMode === 'local_ffmpeg' && localFfmpegViolations.length > 0) {
        message.warning(localFfmpegViolations[0])
        return
      }

      const result = await batchAssemble.mutateAsync({
        video_ids: basket.videos.map((v) => v.id),
        copywriting_ids: basket.copywritings.map((c) => c.id),
        cover_ids: basket.covers.map((c) => c.id),
        audio_ids: basket.audios.map((a) => a.id),
        topic_ids: [],
        account_ids: values.account_id ? [values.account_id] : [],
        profile_id: values.profile_id,
      })

      const createdTasks = Array.isArray(result) ? result : []
      const count = createdTasks.length
      const draftTaskIds = createdTasks
        .filter((task) => task.status === 'draft')
        .map((task) => task.id)
      const readyTaskIds = createdTasks
        .filter((task) => task.status === 'ready')
        .map((task) => task.id)
      message.success(`创建成功，共生成 ${count} 个任务`)
      navigate('/task/list', {
        state: {
          creationSummary: {
            count,
            draftTaskIds,
            readyTaskIds,
          },
        },
      })
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('创建失败')
      }
    }
  }, [form, basket, batchAssemble, localFfmpegViolations, navigate, selectedMode])

  const basketCount = basket.videos.length + basket.copywritings.length + basket.covers.length + basket.audios.length

  const videoColumns: TableColumnsType<VideoResponse> = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '时长', dataIndex: 'duration', key: 'duration', width: 100, render: (d: number | null) => d ? `${d.toFixed(1)}s` : '-' },
    { title: '来源商品', dataIndex: 'product_name', key: 'product_name', width: 150, ellipsis: true, render: (n: string | null) => n || '-' },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: VideoResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => removeFromBasket('videos', record.id)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  const copywritingColumns: TableColumnsType<CopywritingResponse> = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '内容预览', dataIndex: 'content', key: 'content', ellipsis: true, render: (c: string) => c.slice(0, 50) + (c.length > 50 ? '...' : '') },
    { title: '来源商品', dataIndex: 'product_name', key: 'product_name', width: 150, ellipsis: true, render: (n: string | null) => n || '-' },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: CopywritingResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => removeFromBasket('copywritings', record.id)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  const coverColumns: TableColumnsType<CoverResponse> = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '尺寸', key: 'size', width: 120, render: (_: unknown, r: CoverResponse) => r.width && r.height ? `${r.width}x${r.height}` : '-' },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: CoverResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => removeFromBasket('covers', record.id)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  const audioColumns: TableColumnsType<AudioResponse> = [
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: '时长', dataIndex: 'duration', key: 'duration', width: 100, render: (d: number | null) => d ? `${d.toFixed(1)}s` : '-' },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: AudioResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => removeFromBasket('audios', record.id)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  const tabItems = [
    {
      key: 'video',
      label: (
        <Space>
          <VideoCameraOutlined />
          <span>视频</span>
          {basket.videos.length > 0 && <Tag color="blue">{basket.videos.length}</Tag>}
        </Space>
      ),
      children: basket.videos.length === 0 ? (
        <Empty description="暂无视频" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Table<VideoResponse>
          rowKey="id"
          dataSource={basket.videos}
          columns={videoColumns}
          pagination={false}
          size="small"
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
        />
      ),
    },
    {
      key: 'copywriting',
      label: (
        <Space>
          <FileTextOutlined />
          <span>文案</span>
          {basket.copywritings.length > 0 && <Tag color="blue">{basket.copywritings.length}</Tag>}
        </Space>
      ),
      children: basket.copywritings.length === 0 ? (
        <Empty description="暂无文案" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Table<CopywritingResponse>
          rowKey="id"
          dataSource={basket.copywritings}
          columns={copywritingColumns}
          pagination={false}
          size="small"
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
        />
      ),
    },
    {
      key: 'cover',
      label: (
        <Space>
          <PictureOutlined />
          <span>封面</span>
          {basket.covers.length > 0 && <Tag color="blue">{basket.covers.length}</Tag>}
        </Space>
      ),
      children: basket.covers.length === 0 ? (
        <Empty description="暂无封面" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Table<CoverResponse>
          rowKey="id"
          dataSource={basket.covers}
          columns={coverColumns}
          pagination={false}
          size="small"
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
        />
      ),
    },
    {
      key: 'audio',
      label: (
        <Space>
          <AudioOutlined />
          <span>音频</span>
          {basket.audios.length > 0 && <Tag color="blue">{basket.audios.length}</Tag>}
        </Space>
      ),
      children: basket.audios.length === 0 ? (
        <Empty description="暂无音频" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Table<AudioResponse>
          rowKey="id"
          dataSource={basket.audios}
          columns={audioColumns}
          pagination={false}
          size="small"
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
        />
      ),
    },
  ]

  const getCurrentTabCount = () => {
    const countMap: Record<string, number> = {
      video: basket.videos.length,
      copywriting: basket.copywritings.length,
      cover: basket.covers.length,
      audio: basket.audios.length,
    }
    return countMap[activeTab] || 0
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/task/list')}>返回</Button>
        <Title level={4} style={{ margin: 0 }}>兼容任务创建</Title>
      </Space>

      <Card title="商品快速导入" style={{ marginBottom: 16 }}>
        <ProductQuickImport onImport={addToBasket} />
      </Card>

      <Alert
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
        message={`当前页面是兼容 / 高级入口（${creativeFlowMeta.label}）`}
        description="日常创作请先到作品工作台创建作品，再补齐素材与配置。这里保留给兼容迁移、批量装配或排障场景使用。"
        action={(
          <Button size="small" onClick={() => navigate('/creative/workbench')}>
            去作品工作台
          </Button>
        )}
      />

      <Card
        title={
          <Space>
            <span>素材篮</span>
            {basketCount > 0 && <Tag color="blue">{basketCount} 项</Tag>}
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<PlusOutlined />}
              onClick={() => handleOpenModal(activeTab as MaterialType)}
            >
              手动添加
            </Button>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定删除选中的 ${selectedRowKeys.length} 项？`}
                onConfirm={handleBatchDelete}
              >
                <Button danger icon={<DeleteOutlined />}>
                  批量删除
                </Button>
              </Popconfirm>
            )}
            {getCurrentTabCount() > 0 && (
              <Popconfirm
                title="确定清空当前标签页的所有素材？"
                onConfirm={handleClearAll}
              >
                <Button danger icon={<ClearOutlined />}>
                  清空
                </Button>
              </Popconfirm>
            )}
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key)
            setSelectedRowKeys([])
          }}
          items={tabItems}
        />
      </Card>

      <Card title="合成配置">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            profile_id: defaultProfile?.id,
          }}
        >
          {accountsError ? (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
              message="账号列表加载失败"
              description={accountsError instanceof Error ? accountsError.message : '请稍后重试'}
            />
          ) : null}

          <Form.Item
            name="account_id"
            label="发布账号（可选）"
            help="不选则创建无账号任务，发布时随机选择一个可用账号。"
          >
            <Select
              allowClear
              showSearch
              loading={accountsLoading}
              placeholder="可选；不选则发布时随机选择可用账号"
              optionFilterProp="label"
              notFoundContent={accountsError ? '账号加载失败' : undefined}
              options={accounts.map((a: AccountResponseExtended) => ({
                value: a.id,
                label: a.account_name,
              }))}
            />
          </Form.Item>

          <Form.Item name="profile_id" label="合成配置（可选）">
            <Select
              allowClear
              placeholder="选择合成配置（不选则使用默认）"
              optionFilterProp="label"
              options={profiles.map((p: PublishProfileResponse) => ({
                value: p.id,
                label: p.is_default ? `${p.name}（默认）` : p.name,
              }))}
            />
          </Form.Item>

          {profiles.length > 0 && (
            <Form.Item>
              <Text type="secondary" data-testid="task-create-mode-label">
                合成方式：{COMPOSITION_MODE_LABEL[selectedMode] ?? selectedMode}
              </Text>
            </Form.Item>
          )}

          <Form.Item>
            {selectedMode === 'none' ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Alert
                  type="info"
                  showIcon
                  data-testid="task-create-mode-guidance"
                  message="当前为直接发布模式"
                  description="只支持 1 个最终视频、0/1 个文案、0/1 个封面；多话题允许；独立音频输入需先走合成。"
                />
                {directPublishViolations.length > 0 && (
                  <Alert
                    type="warning"
                    showIcon
                    data-testid="task-create-mode-violations"
                    message="当前素材组合不满足直接发布语义"
                    description={
                      <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                        {directPublishViolations.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    }
                  />
                )}
              </Space>
            ) : selectedMode === 'local_ffmpeg' ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Alert
                  type="info"
                  showIcon
                  data-testid="task-create-mode-guidance"
                  message="当前为本地 FFmpeg V1 合成模式"
                  description={
                    <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                      <li>只支持 1 个视频 + 可选 1 个音频。</li>
                      <li>不支持多视频 montage，也不支持多音频混剪。</li>
                      <li>文案、封面、话题仍作为发布层输入，不参与视频合成。</li>
                      <li>合成完成后使用 final video 进入发布链路。</li>
                    </ul>
                  }
                />
                {localFfmpegViolations.length > 0 && (
                  <Alert
                    type="warning"
                    showIcon
                    data-testid="task-create-mode-violations"
                    message="当前素材组合不满足 local_ffmpeg V1 语义"
                    description={
                      <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                        {localFfmpegViolations.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    }
                  />
                )}
              </Space>
            ) : (
              <Alert
                type="info"
                showIcon
                data-testid="task-create-mode-guidance"
                message="当前为 Coze 合成模式"
                description="Coze workflow 负责素材编排与合成；前端负责提交素材，并在产出 final video 后进入发布链路。"
              />
            )}
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                onClick={handleSubmit}
                loading={batchAssemble.isPending}
                disabled={submitDisabled}
                data-testid="task-create-submit"
              >
                创建任务
              </Button>
              <Button onClick={() => navigate('/task/list')}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {modalVisible && (
        <MaterialSelectModal
          visible={modalVisible}
          materialType={modalMaterialType}
          onConfirm={handleModalConfirm}
          onCancel={() => setModalVisible(false)}
        />
      )}
    </div>
  )
}
