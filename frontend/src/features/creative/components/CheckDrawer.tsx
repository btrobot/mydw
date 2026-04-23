import { useEffect } from 'react'
import { DrawerForm } from '@ant-design/pro-components'
import { App, Form, Grid, Input, Radio, Select, Space, Typography } from 'antd'
import type { DrawerProps } from 'antd'

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
const { useBreakpoint } = Grid
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
  const screens = useBreakpoint()
  const [form] = Form.useForm<CheckDrawerFormValues>()
  const { message } = App.useApp()

  const approveMutation = useApproveCreative(creativeId)
  const reworkMutation = useReworkCreative(creativeId)
  const rejectMutation = useRejectCreative(creativeId)

  const submitting = approveMutation.isPending || reworkMutation.isPending || rejectMutation.isPending
  const action = Form.useWatch('action', form) ?? 'APPROVED'
  const drawerWidth = screens.md ? 420 : '100vw'
  const drawerProps = {
    styles: { body: { padding: screens.md ? 24 : 16 } },
    destroyOnClose: true,
    onClose,
    'data-testid': 'creative-check-drawer',
  } as DrawerProps & { 'data-testid': string }

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

  const handleSubmit = async (values: CheckDrawerFormValues) => {
    try {
      if (!creativeId || !version) {
        return false
      }

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
      return true
    } catch (error) {
      handleApiError(error, '提交审核失败')
      return false
    }
  }

  return (
    <DrawerForm<CheckDrawerFormValues>
      title="作品审核"
      width={drawerWidth}
      open={open}
      form={form}
      layout="vertical"
      initialValues={{ action: 'APPROVED' satisfies ReviewAction }}
      onFinish={handleSubmit}
      drawerProps={drawerProps}
      submitter={{
        searchConfig: {
          resetText: '取消',
          submitText: '提交审核',
        },
        submitButtonProps: {
          loading: submitting,
          'data-testid': 'creative-review-submit',
        },
        resetButtonProps: {
          'data-testid': 'creative-review-cancel',
        },
      }}
    >
      {version ? (
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Text strong>{getVersionTitle(version)}</Text>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              {getVersionLabel(version.version_no)} / Package #{version.package_record_id ?? '-'}
            </Paragraph>
          </div>

          <Paragraph type="secondary" style={{ margin: 0 }}>
            审核结论会直接更新当前版本状态，历史审核记录会保留在版本时间线中。
          </Paragraph>

          <>
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
                rules={[{ required: true, message: '请选择具体返工类型' }]}
              >
                <Select
                  placeholder="请选择返工类型"
                  options={REWORK_OPTIONS}
                  data-testid="creative-rework-type"
                />
              </Form.Item>
            ) : null}

            <Form.Item name="note" label="审核备注">
              <TextArea
                rows={5}
                maxLength={400}
                placeholder="可填写给运营或制作同学的补充说明"
                showCount
              />
            </Form.Item>
          </>
        </Space>
      ) : null}
    </DrawerForm>
  )
}
