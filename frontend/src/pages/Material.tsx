import { useEffect, useState } from 'react'
import { Table, Button, Space, Tabs, Card, List, Typography, message, Upload, Row, Col } from 'antd'
import { UploadOutlined, SyncOutlined, ScanOutlined, FileOutlined } from '@ant-design/icons'
import { api } from '../services/api'

const { Text } = Typography

interface Material {
  id: number
  type: string
  name: string
  path: string | null
  content: string | null
  size: number | null
  created_at: string
}

interface FileInfo {
  name: string
  path: string
  size: number
  type: string
}

interface MaterialStats {
  video: { count: number; size: number }
  text: { count: number; size: number }
  cover: { count: number; size: number }
  topic: { count: number; size: number }
  audio: { count: number; size: number }
  _total: { count: number; size: number }
}

const typeLabels: Record<string, string> = {
  video: '视频',
  text: '文案',
  cover: '封面',
  topic: '话题',
  audio: '音频',
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function Material() {
  const [materials, setMaterials] = useState<Material[]>([])
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [importing, setImporting] = useState(false)
  const [activeTab, setActiveTab] = useState('video')
  const [stats, setStats] = useState<MaterialStats | null>(null)

  useEffect(() => {
    fetchStats()
    fetchMaterials()
    fetchFiles()
  }, [])

  useEffect(() => {
    fetchMaterials()
    fetchFiles()
  }, [activeTab])

  const fetchStats = async () => {
    try {
      const res = await api.get('/materials/stats')
      setStats(res.data)
    } catch (error) {
      console.error('获取统计失败:', error)
    }
  }

  const fetchMaterials = async () => {
    try {
      setLoading(true)
      const res = await api.get(`/materials?type=${activeTab}`)
      setMaterials(res.data.items || [])
    } catch (error) {
      message.error('获取素材失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchFiles = async () => {
    try {
      const res = await api.get(`/materials/path/${activeTab}`)
      setFiles(res.data.files || [])
    } catch (error) {
      console.error('获取文件失败:', error)
    }
  }

  const handleScan = async () => {
    try {
      setScanning(true)
      const res = await api.post('/materials/scan', { type: activeTab })
      message.success(`扫描完成，发现 ${res.data.total} 个文件`)
      fetchFiles()
    } catch (error) {
      message.error('扫描失败')
    } finally {
      setScanning(false)
    }
  }

  const handleImport = async () => {
    try {
      setImporting(true)
      const res = await api.post(`/materials/import/${activeTab}`)
      message.success(`导入完成: 成功 ${res.data.success}, 失败 ${res.data.failed}`)
      fetchMaterials()
      fetchStats()
    } catch (error) {
      message.error('导入失败')
    } finally {
      setImporting(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/materials/${id}`)
      message.success('删除成功')
      fetchMaterials()
      fetchStats()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <FileOutlined />
          <Text>{name}</Text>
        </Space>
      ),
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (content: string | null) => content ? (
        <Text type="secondary" style={{ maxWidth: 300 }}>{content.substring(0, 50)}...</Text>
      ) : '-',
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size: number | null) => formatSize(size || 0),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Material) => (
        <Button type="link" danger size="small" onClick={() => handleDelete(record.id)}>
          删除
        </Button>
      ),
    },
  ]

  const tabItems = [
    { key: 'video', label: `视频 (${stats?.video?.count || 0})` },
    { key: 'text', label: `文案 (${stats?.text?.count || 0})` },
    { key: 'cover', label: `封面 (${stats?.cover?.count || 0})` },
    { key: 'topic', label: `话题 (${stats?.topic?.count || 0})` },
    { key: 'audio', label: `音频 (${stats?.audio?.count || 0})` },
  ]

  const getUploadAccept = () => {
    const accepts: Record<string, string> = {
      video: 'video/*',
      audio: 'audio/*',
      cover: 'image/*',
      text: 'text/plain',
      topic: 'text/plain',
    }
    return accepts[activeTab] || '*'
  }

  return (
    <>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic title="视频" value={stats?.video?.count || 0} suffix={`(${formatSize(stats?.video?.size || 0)})`} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="文案" value={stats?.text?.count || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="封面" value={stats?.cover?.count || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="话题" value={stats?.topic?.count || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="音频" value={stats?.audio?.count || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="总计" value={stats?._total?.count || 0} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ marginBottom: 16 }}
      />

      <Space style={{ marginBottom: 16 }}>
        <Upload
          accept={getUploadAccept()}
          showUploadList={false}
          customRequest={async ({ file, onSuccess }) => {
            try {
              const formData = new FormData()
              formData.append('file', file as File)
              await api.post(`/materials/upload/${activeTab}`, formData)
              message.success('上传成功')
              fetchMaterials()
              fetchFiles()
              fetchStats()
              onSuccess?.({})
            } catch (error) {
              message.error('上传失败')
            }
          }}
        >
          <Button icon={<UploadOutlined />}>上传{typeLabels[activeTab]}</Button>
        </Upload>

        <Button icon={<ScanOutlined />} onClick={handleScan} loading={scanning}>
          扫描本地
        </Button>

        <Button icon={<SyncOutlined />} onClick={handleImport} loading={importing}>
          导入到数据库
        </Button>

        <Button icon={<FileOutlined />} onClick={fetchFiles}>
          刷新
        </Button>
      </Space>

      <Space style={{ width: '100%' }} size="large">
        <Card title="素材库" style={{ flex: 1 }} extra={<Text type="secondary">{materials.length} 条</Text>}>
          <Table
            columns={columns}
            dataSource={materials}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            size="small"
          />
        </Card>

        <Card
          title="本地文件"
          extra={<Text type="secondary">{files.length} 个文件</Text>}
          style={{ flex: 1, maxHeight: 500, overflow: 'auto' }}
        >
          <List
            size="small"
            dataSource={files}
            renderItem={(item: FileInfo) => (
              <List.Item>
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Space>
                    <FileOutlined />
                    <Text>{item.name}</Text>
                  </Space>
                  <Text type="secondary">{formatSize(item.size)}</Text>
                </Space>
              </List.Item>
            )}
            locale={{ emptyText: '暂无文件，点击"扫描本地"查找素材' }}
          />
        </Card>
      </Space>
    </>
  )
}

// 简单的统计组件
function Statistic({ title, value, suffix, valueStyle }: { title: string; value: number; suffix?: string; valueStyle?: any }) {
  return (
    <div>
      <Text type="secondary" style={{ fontSize: 12 }}>{title}</Text>
      <div>
        <Text style={{ fontSize: 20, ...valueStyle }}>{value}</Text>
        {suffix && <Text type="secondary" style={{ fontSize: 12 }}> {suffix}</Text>}
      </div>
    </div>
  )
}
