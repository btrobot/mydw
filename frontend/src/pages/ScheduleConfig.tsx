import { useEffect } from 'react'
import { Card, Form, InputNumber, Switch, Button, Divider, message, Space } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { useScheduleConfig, useUpdateScheduleConfig } from '../hooks/useScheduleConfig'

import type { ScheduleConfigRequest } from '@/api'
import { InlineNotice } from '@/components/feedback/InlineNotice'
import { PageHeader } from '@/components/ui/PageHeader'

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
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <PageHeader
        title="\u8c03\u5ea6\u914d\u7f6e"
        subtitle="\u5c06\u53d1\u5e03\u65f6\u95f4\u7a97\u53e3\u3001\u8282\u594f\u4e0e\u81ea\u52a8\u5316\u5f00\u5173\u6536\u675f\u5728\u540c\u4e00\u4e2a\u7b56\u7565\u9875\u5185\uff0c\u907f\u514d\u628a\u300c\u4ec0\u4e48\u65f6\u5019\u53d1\u300d\u548c\u300c\u600e\u6837\u53d1\u300d\u5206\u6563\u5230\u591a\u5904\u3002"
        extra={(
          <Button type="primary" icon={<SaveOutlined />} loading={loading} onClick={handleSave}>
            {'\u4fdd\u5b58\u914d\u7f6e'}
          </Button>
        )}
      />
      <InlineNotice
        message="\u5148\u5b9a\u65f6\u95f4\u8303\u56f4\u548c\u53d1\u5e03\u95f4\u9694\uff0c\u518d\u51b3\u5b9a\u662f\u5426\u4e71\u5e8f\u4e0e\u81ea\u52a8\u542f\u52a8"
        description="\u8fd9\u4e2a\u9875\u53ea\u627f\u8f7d\u53d1\u5e03\u7b56\u7565\u53c2\u6570\uff1b\u5177\u4f53\u53d1\u5e03\u961f\u5217\u4ecd\u7136\u5728\u4efb\u52a1\u4e0e\u4f5c\u54c1\u5de5\u4f5c\u53f0\u4e2d\u89c2\u5bdf\u4e0e\u5904\u7406\u3002"
      />
      <Card>
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
    </Space>
  )
}
