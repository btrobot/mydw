import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Form,
  InputNumber,
  Switch,
  Button,
  Space,
  Divider,
  message,
  Table,
  Modal,
  Input,
  Select,
  Tag,
  Popconfirm,
  Tooltip,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { SaveOutlined, PlusOutlined, EditOutlined, DeleteOutlined, StarOutlined } from '@ant-design/icons'
import { api } from '../services/api'
import {
  useProfiles,
  useCreateProfile,
  useUpdateProfile,
  useDeleteProfile,
  useSetDefaultProfile,
} from '../hooks/useProfile'
import type { PublishProfileResponse, PublishProfileCreate, PublishProfileUpdate, CompositionMode } from '../hooks/useProfile'

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
          global_topic_ids: editing.global_topic_ids.join(', '),
          auto_retry: editing.auto_retry,
          max_retry_count: editing.max_retry_count,
        })
      } else {
        form.resetFields()
        form.setFieldsValue({
          composition_mode: 'none',
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
      title={editing ? '编辑配置档' : '新建配置档'}
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
          label="配置档名称"
          rules={[{ required: true, message: '请输入名称' }, { max: 128, message: '最多 128 个字符' }]}
        >
          <Input placeholder="例如：默认配置" />
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

// ============ Profile Section ============

function ProfileSection() {
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
    coze: 'Coze',
    local_ffmpeg: 'FFmpeg',
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
          <Tooltip title={record.is_default ? '默认配置档不可删除' : '删除'}>
            <Popconfirm
              title="确认删除该配置档？"
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
    <>
      <Card
        title="配置档管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建配置档
          </Button>
        }
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
    </>
  )
}

// ============ Settings Page ============

export default function Settings() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const res = await api.get('/publish/config')
      form.setFieldsValue({
        interval_minutes: res.data.interval_minutes,
        start_hour: res.data.start_hour,
        end_hour: res.data.end_hour,
        max_per_account_per_day: res.data.max_per_account_per_day,
        shuffle: res.data.shuffle,
        auto_start: res.data.auto_start,
      })
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      }
    }
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      const values = form.getFieldsValue()
      await api.put('/publish/config', values)
      message.success('保存成功')
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('保存失败')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card
        title="发布策略"
        extra={
          <Button type="primary" icon={<SaveOutlined />} loading={loading} onClick={handleSave}>
            保存配置
          </Button>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="interval_minutes" label="发布间隔（分钟）" tooltip="每次发布之间的等待时间">
            <InputNumber min={1} max={1440} style={{ width: 200 }} />
          </Form.Item>

          <Form.Item label="发布时间范围">
            <Space>
              <Form.Item name="start_hour" noStyle>
                <InputNumber min={0} max={23} style={{ width: 80 }} placeholder="开始小时" />
              </Form.Item>
              <span> - </span>
              <Form.Item name="end_hour" noStyle>
                <InputNumber min={0} max={23} style={{ width: 80 }} placeholder="结束小时" />
              </Form.Item>
              <span>点</span>
            </Space>
          </Form.Item>

          <Form.Item name="max_per_account_per_day" label="单账号每日最大发布条数">
            <InputNumber min={1} max={100} style={{ width: 200 }} />
          </Form.Item>

          <Divider />

          <Form.Item name="shuffle" label="乱序发布" valuePropName="checked" tooltip="打乱任务顺序发布">
            <Switch />
          </Form.Item>

          <Form.Item name="auto_start" label="自动开始" valuePropName="checked" tooltip="程序启动时自动开始发布">
            <Switch />
          </Form.Item>
        </Form>
      </Card>

      <ProfileSection />

      <Card title="素材路径">
        <p>当前素材存储路径: <code>D:\系统\桌面\得物剪辑\待上传数据</code></p>
      </Card>

      <Card title="数据管理">
        <Space>
          <Button onClick={async () => {
            try {
              const res = await api.post('/system/backup')
              message.success(`备份已保存: ${res.data.backup_file}`)
            } catch (error: unknown) {
              if (error instanceof Error) {
                message.error(error.message)
              } else {
                message.error('备份失败')
              }
            }
          }}>
            备份数据
          </Button>
        </Space>
      </Card>
    </Space>
  )
}
