import { useState } from 'react'
import { Card, Form, InputNumber, Switch, TimePicker, Button, Space, Divider, message } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { api } from '../services/api'

export default function Settings() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useState(() => {
    fetchConfig()
  })

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
    } catch (error) {
      console.error('获取配置失败:', error)
    }
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      const values = form.getFieldsValue()
      await api.put('/publish/config', values)
      message.success('保存成功')
    } catch (error) {
      message.error('保存失败')
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

      <Card title="素材路径">
        <p>当前素材存储路径: <code>D:\系统\桌面\得物剪辑\待上传数据</code></p>
      </Card>

      <Card title="数据管理">
        <Space>
          <Button onClick={async () => {
            try {
              const res = await api.post('/system/backup')
              message.success(`备份已保存: ${res.data.backup_file}`)
            } catch (error) {
              message.error('备份失败')
            }
          }}>
            备份数据
          </Button>
        </Space>
      </Card>
    </Space>
  )
}
