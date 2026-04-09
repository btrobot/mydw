import { Card, Button, Space, message } from 'antd'
import { api } from '../services/api'

// ============ Settings Page ============

export default function Settings() {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
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
