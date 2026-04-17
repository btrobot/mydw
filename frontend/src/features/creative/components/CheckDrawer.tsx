import { useEffect } from 'react'
import { App, Button, Drawer, Form, Input, Radio, Select, Space, Typography } from 'antd'

import type {
  CreativeApproveRequest,
  CreativeRejectRequest,
  CreativeReworkRequest,
} from '@/api'
import { handleApiError } from '@/utils/error'

import {
  useApproveCreative,
  useRejectCreative,
  useReworkCreative,
} from '../hooks/useCreatives'
import type { CreativeVersionSummary } from '../types/creative'
import { getVersionLabel, getVersionTitle } from '../types/creative'

const { Paragraph, Text } = Typography
const { TextArea } = Input

type ReviewAction = 'APPROVED' | 'REWORK_REQUIRED' | 'REJECTED'

interface CheckDrawerFormValues {
  action: ReviewAction
  note?: string
  rework_type?: string
}

interface CheckDrawerProps {
  creativeId?: number
  open: boolean
  version?: CreativeVersionSummary | null
  onClose: () => void
}

const REWORK_OPTIONS = [
  { label: '文案返工', value: 'COPY_REWORK' },
  { label: '素材返工', value: 'ASSET_REWORK' },
  { label: '镜头返工', value: 'SHOT_REWORK' },
  { label: '结构返工', value: 'STRUCTURE_REWORK' },
]

export default function CheckDrawer({
  creativeId,
  open,
  version,
  onClose,
}: CheckDrawerProps) {
  const [form] = Form.useForm<CheckDrawerFormValues>()
  const { message } = App.useApp()

  const approveMutation = useApproveCreative(creativeId)
  const reworkMutation = useReworkCreative(creativeId)
  const rejectMutation = useRejectCreative(creativeId)

  const submitting = approveMutation.isPending || reworkMutation.isPending || rejectMutation.isPending
  const action = Form.useWatch('action', form) ?? 'APPROVED'

  useEffect(() => {
    if (open) {
      form.setFieldsValue({
        action: 'APPROVED',
        note: undefined,
        rework_type: undefined,
      })
    } else {
      form.resetFields()
    }
  }, [form, open, version?.id])

  const handleSubmit = async () => {
    try {
      if (!creativeId || !version) {
        return
      }

      const values = await form.validateFields()

      if (values.action === 'APPROVED') {
        const payload: CreativeApproveRequest = {
          version_id: version.id,
          note: values.note?.trim() || undefined,
        }
        await approveMutation.mutateAsync(payload)
        message.success('已完成通过审核')
      } else if (values.action === 'REWORK_REQUIRED') {
        const payload: CreativeReworkRequest = {
          version_id: version.id,
          rework_type: values.rework_type,
          note: values.note?.trim() || undefined,
        }
        await reworkMutation.mutateAsync(payload)
        message.success('已记录返工要求')
      } else {
        const payload: CreativeRejectRequest = {
          version_id: version.id,
          note: values.note?.trim() || undefined,
        }
        await rejectMutation.mutateAsync(payload)
        message.success('已驳回当前版本')
      }

      onClose()
    } catch (error) {
      if (
        typeof error === 'object'
        && error !== null
        && 'errorFields' in error
      ) {
        return
      }

      handleApiError(error, '提交审核失败')
    }
  }

  return (
    <Drawer
      title="作品审核"
      width={420}
      open={open}
      onClose={onClose}
      destroyOnClose
      data-testid="creative-check-drawer"
      extra={(
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button
            type="primary"
            loading={submitting}
            data-testid="creative-review-submit"
            onClick={() => void handleSubmit()}
          >
            提交审核
          </Button>
        </Space>
      )}
    >
      {version ? (
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong>{getVersionTitle(version)}</Text>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              {getVersionLabel(version.version_no)} / Package #{version.package_record_id ?? '-'}
            </Paragraph>
          </div>

          <Form
            form={form}
            layout="vertical"
            initialValues={{ action: 'APPROVED' satisfies ReviewAction }}
          >
            <Form.Item
              name="action"
              label="审核动作"
              rules={[{ required: true, message: '请选择审核动作' }]}
            >
              <Radio.Group optionType="button" buttonStyle="solid">
                <Radio.Button value="APPROVED" data-testid="creative-review-action-approve">
                  通过
                </Radio.Button>
                <Radio.Button value="REWORK_REQUIRED" data-testid="creative-review-action-rework">
                  返工
                </Radio.Button>
                <Radio.Button value="REJECTED" data-testid="creative-review-action-reject">
                  驳回
                </Radio.Button>
              </Radio.Group>
            </Form.Item>

            {action === 'REWORK_REQUIRED' ? (
              <Form.Item
                name="rework_type"
                label="返工类型"
                rules={[{ required: true, message: '返工必须选择返工类型' }]}
              >
                <Select
                  placeholder="请选择返工类型"
                  options={REWORK_OPTIONS}
                  data-testid="creative-rework-type"
                />
              </Form.Item>
            ) : null}

            <Form.Item name="note" label="审核说明">
              <TextArea
                rows={5}
                maxLength={400}
                placeholder="补充审核意见，便于后续追溯"
                showCount
              />
            </Form.Item>
          </Form>
        </Space>
      ) : null}
    </Drawer>
  )
}
