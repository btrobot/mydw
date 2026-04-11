import { useEffect } from 'react'
import { Card, Form, InputNumber, Switch, Button, Divider, message, Space } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { useScheduleConfig, useUpdateScheduleConfig } from '../hooks/useScheduleConfig'

import type { ScheduleConfigRequest } from '@/api'

export default function ScheduleConfig() {
  const [form] = Form.useForm<ScheduleConfigRequest>()
  const { data, isLoading } = useScheduleConfig()
  const updateScheduleConfig = useUpdateScheduleConfig()

  useEffect(() => {
    if (data) {
      form.setFieldsValue({
        interval_minutes: data.interval_minutes,
        start_hour: data.start_hour,
        end_hour: data.end_hour,
        max_per_account_per_day: data.max_per_account_per_day,
        shuffle: data.shuffle,
        auto_start: data.auto_start,
      })
    }
  }, [data, form])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      await updateScheduleConfig.mutateAsync(values)
      message.success('保存成功')
    } catch (error: unknown) {
      if (error instanceof Error && error.message !== 'Validation failed') {
        message.error(error.message)
      }
    }
  }

  const loading = isLoading || updateScheduleConfig.isPending

  return (
    <Card
      title="调度配置"
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
  )
}
