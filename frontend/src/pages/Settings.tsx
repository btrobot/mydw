import { useEffect } from 'react'
import { Alert, App, Button, Card, Descriptions, Form, Input, Select, Space, Switch, Typography } from 'antd'
import { useBackup, useSystemConfig, useUpdateSystemConfig } from '@/hooks/useSystem'
import { creativeFlowModeMeta } from '@/features/creative/creativeFlow'

const { Paragraph, Text } = Typography

// ============ Settings Page ============

export default function Settings() {
  const { message } = App.useApp()
  const [form] = Form.useForm<{
    material_base_path: string
    creative_flow_mode: 'task_first' | 'dual' | 'creative_first'
    creative_flow_shadow_compare: boolean
  }>()
  const { data: systemConfig, isLoading } = useSystemConfig()
  const updateSystemConfig = useUpdateSystemConfig()
  const backup = useBackup()

  useEffect(() => {
    if (systemConfig) {
      form.setFieldsValue({
        material_base_path: systemConfig.material_base_path,
        creative_flow_mode: systemConfig.creative_flow_mode,
        creative_flow_shadow_compare: systemConfig.creative_flow_shadow_compare,
      })
    }
  }, [form, systemConfig])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      await updateSystemConfig.mutateAsync({
        material_base_path: values.material_base_path,
        creative_flow_mode: values.creative_flow_mode,
        creative_flow_shadow_compare: values.creative_flow_shadow_compare,
      })
      message.success('运行时设置已更新')
    } catch (error: unknown) {
      if (error instanceof Error && error.message !== 'Validation failed') {
        message.error(error.message)
      }
    }
  }

  const handleBackup = async () => {
    try {
      const result = await backup.mutateAsync({ include_logs: false })
      message.success(`备份已保存: ${result.backup_file}`)
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('备份失败')
      }
    }
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="运行时设置">
        <Paragraph type="secondary">
          当前受支持的 runtime-config 项：<Text code>material_base_path</Text>、
          <Text code>creative_flow_mode</Text>、<Text code>creative_flow_shadow_compare</Text>。
          保存后会写入 <Text code>data/system_config.json</Text>，不需要改动启动期环境变量。
        </Paragraph>
        <Form form={form} layout="vertical">
          <Form.Item
            name="material_base_path"
            label="素材根目录"
            rules={[{ required: true, message: '请输入素材根目录' }]}
          >
            <Input placeholder="请输入素材根目录" />
          </Form.Item>

          <Form.Item name="creative_flow_mode" label="作品驱动入口模式" rules={[{ required: true, message: '请选择入口模式' }]}>
            <Select
              options={Object.entries(creativeFlowModeMeta).map(([value, meta]) => ({
                value,
                label: `${meta.label}：${meta.description}`,
              }))}
            />
          </Form.Item>

          <Form.Item
            name="creative_flow_shadow_compare"
            label="双轨对账（Shadow Compare）"
            valuePropName="checked"
          >
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>

          <Button type="primary" onClick={handleSave} loading={updateSystemConfig.isPending || isLoading}>
            保存运行时设置
          </Button>
        </Form>
      </Card>

      <Card title="只读系统信息">
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="日志级别">
            <Space direction="vertical" size={0}>
              <Text>{systemConfig?.log_level ?? '-'}</Text>
              <Text type="secondary">启动期配置，只读；如需调整请修改 .env / backend/core/config.py 后重启。</Text>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="自动备份">
            <Space direction="vertical" size={0}>
              <Text>未开放（当前不支持运行时配置）</Text>
              <Text type="secondary">auto_backup 仍是兼容占位字段；不会在运行时保存，也不会静默成功。</Text>
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="数据管理">
        <Alert
          type="info"
          showIcon
          message="备份范围说明"
          description="当前备份会生成最小真实备份产物：数据库快照（如存在）、运行时配置快照与元数据清单（manifest）；不包含媒体文件，也不提供完整 restore 工作流。"
          style={{ marginBottom: 16 }}
        />
        <Paragraph type="secondary">
          备份清单默认写入 <Text code>data/backups/&lt;timestamp&gt;/manifest.json</Text>，用于说明已经导出了什么、
          没有导出什么，以及当前有效的系统设置。
        </Paragraph>
        <Space>
          <Button onClick={handleBackup} loading={backup.isPending}>
            备份数据
          </Button>
        </Space>
      </Card>

      <Card title="说明">
        <Paragraph>
          <Text strong>启动期配置：</Text> 如日志级别等仍由 <code>.env / backend/core/config.py</code> 决定，
          当前不会在运行时写回。
        </Paragraph>
        <Paragraph style={{ marginBottom: 0 }}>
          <Text strong>Unsupported settings policy：</Text> 未进入 truth matrix 的字段不会出现在可编辑 UI 中；
          如果旧调用方仍传入 <Text code>auto_backup</Text> 或 <Text code>log_level</Text>，后端会明确拒绝，
          而不是伪装“保存成功”。
        </Paragraph>
      </Card>
    </Space>
  )
}
