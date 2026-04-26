import { useState, useEffect, useCallback } from 'react'
import {
  Alert,
  Card,
  Form,
  Button,
  Space,
  Table,
  Modal,
  Input,
  InputNumber,
  Switch,
  Select,
  Tag,
  Popconfirm,
  Tooltip,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, StarOutlined } from '@ant-design/icons'
import {
  useProfiles,
  useCreateProfile,
  useUpdateProfile,
  useDeleteProfile,
  useSetDefaultProfile,
} from '../hooks/useProfile'
import type { PublishProfileResponse, PublishProfileCreate, PublishProfileUpdate, CompositionMode } from '../hooks/useProfile'
import { InlineNotice } from '@/components/feedback/InlineNotice'
import { PageHeader } from '@/components/ui/PageHeader'

// ============ Profile Form Values ============

interface ProfileFormValues {
  name: string
  composition_mode: CompositionMode
  coze_workflow_id: string
  global_topic_ids: string
  auto_retry: boolean
  max_retry_count: number
}

// ============ Profile Modal ============

interface ProfileModalProps {
  open: boolean
  editing: PublishProfileResponse | null
  onClose: () => void
}

const compositionModeGuidance: Record<CompositionMode, { message: string; points: string[] }> = {
  none: {
    message: '直接发布模式',
    points: [
      '只适合已经准备好最终视频的任务。',
      '直接发布只支持 1 个最终视频、0/1 个文案、0/1 个封面。',
      '独立音频输入需先走合成流程。',
    ],
  },
  coze: {
    message: 'Coze 工作流模式',
    points: [
      '由 Coze workflow 负责素材编排与合成。',
      '前端只负责提交素材，并在产出 final video 后进入发布链路。',
      '适合仍依赖外部工作流的组合场景。',
    ],
  },
  local_ffmpeg: {
    message: '本地 FFmpeg V1 模式',
    points: [
      '当前只支持 1 个视频 + 可选 1 个音频。',
      '不支持多视频 montage，也不支持多音频混剪。',
      '文案、封面、话题仍作为发布层输入，不参与视频合成。',
    ],
  },
}

function ProfileModal({ open, editing, onClose }: ProfileModalProps) {
  const [form] = Form.useForm<ProfileFormValues>()
  const createProfile = useCreateProfile()
  const updateProfile = useUpdateProfile()

  useEffect(() => {
    if (open) {
      if (editing) {
        form.setFieldsValue({
          name: editing.name,
          composition_mode: editing.composition_mode,
          coze_workflow_id: editing.coze_workflow_id ?? '',
          global_topic_ids: (editing.global_topic_ids ?? []).join(', '),
          auto_retry: editing.auto_retry,
          max_retry_count: editing.max_retry_count,
        })
      } else {
        form.resetFields()
        form.setFieldsValue({
          composition_mode: 'local_ffmpeg',
          auto_retry: true,
          max_retry_count: 3,
          global_topic_ids: '',
        })
      }
    }
  }, [open, editing, form])

  const parseTopicIds = (raw: string): number[] => {
    if (!raw.trim()) return []
    return raw
      .split(/[,，\s]+/)
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !isNaN(n))
  }

  const handleOk = useCallback(async () => {
    try {
      const values = await form.validateFields()
      const topicIds = parseTopicIds(values.global_topic_ids)

      if (editing) {
        const update: PublishProfileUpdate = {
          name: values.name,
          composition_mode: values.composition_mode,
          coze_workflow_id: values.coze_workflow_id || null,
          global_topic_ids: topicIds,
          auto_retry: values.auto_retry,
          max_retry_count: values.max_retry_count,
        }
        await updateProfile.mutateAsync({ id: editing.id, data: update })
      } else {
        const create: PublishProfileCreate = {
          name: values.name,
          composition_mode: values.composition_mode,
          coze_workflow_id: values.coze_workflow_id || null,
          global_topic_ids: topicIds,
          auto_retry: values.auto_retry,
          max_retry_count: values.max_retry_count,
        }
        await createProfile.mutateAsync(create)
      }
      onClose()
    } catch (error: unknown) {
      // form validation errors are handled by antd; API errors handled in hooks
      if (error instanceof Error && error.message !== 'Validation failed') {
        // already shown by hook onError
      }
    }
  }, [form, editing, createProfile, updateProfile, onClose])

  const isPending = createProfile.isPending || updateProfile.isPending

  return (
    <Modal
      title={editing ? '编辑合成配置' : '新建合成配置'}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={isPending}
      destroyOnClose
      width={520}
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          name="name"
          label="合成配置名称"
          rules={[{ required: true, message: '请输入名称' }, { max: 128, message: '最多 128 个字符' }]}
        >
          <Input placeholder="例如：默认合成配置" />
        </Form.Item>

        <Form.Item
          name="composition_mode"
          label="合成方式"
          rules={[{ required: true, message: '请选择合成方式' }]}
        >
          <Select
            options={[
              { value: 'none', label: '不合成' },
              { value: 'coze', label: 'Coze 工作流' },
              { value: 'local_ffmpeg', label: '本地 FFmpeg' },
            ]}
          />
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prev: ProfileFormValues, cur: ProfileFormValues) =>
            prev.composition_mode !== cur.composition_mode
          }
        >
          {({ getFieldValue }) => {
            const mode = getFieldValue('composition_mode') as CompositionMode | undefined
            const guidance = mode ? compositionModeGuidance[mode] : null
            if (!guidance) return null

            return (
              <Alert
                type="info"
                showIcon
                data-testid="profile-composition-mode-guidance"
                style={{ marginBottom: 16 }}
                message={guidance.message}
                description={
                  <ul style={{ margin: 0, paddingInlineStart: 18 }}>
                    {guidance.points.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                }
              />
            )
          }}
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prev: ProfileFormValues, cur: ProfileFormValues) =>
            prev.composition_mode !== cur.composition_mode
          }
        >
          {({ getFieldValue }) =>
            getFieldValue('composition_mode') === 'coze' ? (
              <Form.Item name="coze_workflow_id" label="Coze Workflow ID">
                <Input placeholder="请输入 Coze Workflow ID" />
              </Form.Item>
            ) : null
          }
        </Form.Item>

        <Form.Item
          name="global_topic_ids"
          label="全局话题 ID"
          tooltip="多个 ID 用逗号或空格分隔"
        >
          <Input placeholder="例如：123, 456, 789" />
        </Form.Item>

        <Form.Item name="auto_retry" label="自动重试" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item name="max_retry_count" label="最大重试次数">
          <InputNumber min={0} max={10} style={{ width: 120 }} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

// ============ Profile Management Page ============

export default function ProfileManagement() {
  const { data, isLoading } = useProfiles()
  const deleteProfile = useDeleteProfile()
  const setDefault = useSetDefaultProfile()

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<PublishProfileResponse | null>(null)

  const handleCreate = useCallback(() => {
    setEditing(null)
    setModalOpen(true)
  }, [])

  const handleEdit = useCallback((record: PublishProfileResponse) => {
    setEditing(record)
    setModalOpen(true)
  }, [])

  const handleClose = useCallback(() => {
    setModalOpen(false)
    setEditing(null)
  }, [])

  const compositionModeLabel: Record<CompositionMode, string> = {
    none: '不合成',
    coze: 'Coze 工作流',
    local_ffmpeg: '本地 FFmpeg',
  }

  const columns: TableColumnsType<PublishProfileResponse> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <Space>
          {name}
          {record.is_default && <Tag color="blue">默认</Tag>}
        </Space>
      ),
    },
    {
      title: '合成方式',
      dataIndex: 'composition_mode',
      key: 'composition_mode',
      render: (mode: CompositionMode) => compositionModeLabel[mode] ?? mode,
    },
    {
      title: '自动重试',
      dataIndex: 'auto_retry',
      key: 'auto_retry',
      render: (val: boolean, record) =>
        val ? `是（最多 ${record.max_retry_count} 次）` : '否',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          {!record.is_default && (
            <Tooltip title="设为默认">
              <Button
                size="small"
                icon={<StarOutlined />}
                onClick={() => setDefault.mutate(record.id)}
                loading={setDefault.isPending}
              />
            </Tooltip>
          )}
          <Tooltip title={record.is_default ? '默认合成配置不可删除' : '删除'}>
            <Popconfirm
              title="确认删除该合成配置？"
              onConfirm={() => deleteProfile.mutate(record.id)}
              disabled={record.is_default}
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_default}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <PageHeader
        title="\u53d1\u5e03\u914d\u7f6e"
        subtitle="\u5c06\u5408\u6210\u65b9\u5f0f\u3001\u5168\u5c40\u8bdd\u9898\u4e0e\u91cd\u8bd5\u7b56\u7565\u6536\u675f\u4e3a\u7a33\u5b9a\u7684\u53d1\u5e03\u6863\u6848\uff0c\u8ba9\u521b\u5efa\u3001\u7f16\u8f91\u548c\u9ed8\u8ba4\u5207\u6362\u90fd\u5728\u540c\u4e00\u5c42\u7ea7\u5185\u5b8c\u6210\u3002"
        extra={(
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            {'\u65b0\u5efa\u5408\u6210\u914d\u7f6e'}
          </Button>
        )}
      />
      <InlineNotice
        message="\u9ed8\u8ba4\u53d1\u5e03\u914d\u7f6e\u4f1a\u76f4\u63a5\u5f71\u54cd\u521b\u5efa\u4efb\u52a1\u4e0e\u4f5c\u54c1\u7f16\u6392\u9636\u6bb5\u7684\u7d20\u6750\u5408\u6210\u8def\u5f84"
        description="\u5efa\u8bae\u5148\u7a33\u5b9a\u9ed8\u8ba4\u6863\u6848\uff0c\u518d\u4e3a\u7279\u6b8a\u573a\u666f\u6dfb\u52a0\u4f8b\u5916\u914d\u7f6e\uff1b\u5220\u9664\u88ab\u4f9d\u8d56\u7684\u914d\u7f6e\u524d\uff0c\u5148\u5b8c\u6210\u66ff\u4ee3\u6216\u9ed8\u8ba4\u5207\u6362\u3002"
      />
      <Card
        title="合成配置列表"
      >
        <Table<PublishProfileResponse>
          rowKey="id"
          dataSource={data?.items ?? []}
          columns={columns}
          loading={isLoading}
          pagination={false}
          size="small"
        />
      </Card>

      <ProfileModal open={modalOpen} editing={editing} onClose={handleClose} />
    </Space>
  )
}
