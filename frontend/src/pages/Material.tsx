import { useEffect, useState } from 'react'
import { Table, Tag, Button, Space, Tabs, Card, List, Typography, message, Upload } from 'antd'
import { PlusOutlined, DeleteOutlined, FolderOpenOutlined, UploadOutlined } from '@ant-design/icons'
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
}

export default function Material() {
  const [materials, setMaterials] = useState<Material[]>([])
  const [files, setFiles] = useState<Record<string, FileInfo[]>>({})
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('video')

  useEffect(() => {
    fetchMaterials()
    fetchFiles()
  }, [activeTab])

  const fetchMaterials = async () => {
    try {
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
      const types = ['video', 'text', 'cover', 'topic', 'audio']
      const results: Record<string, FileInfo[]> = {}

      for (const type of types) {
        const res = await api.get(`/materials/path/${type}`)
        results[type] = res.data.files || []
      }

      setFiles(results)
    } catch (error) {
      console.error('获取文件失败:', error)
    }
  }

  const handleDelete = async (id: number) => {
    await api.delete(`/materials/${id}`)
    message.success('删除成功')
    fetchMaterials()
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number | null) => size ? `${(size / 1024 / 1024).toFixed(2)} MB` : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Material) => (
        <Button type="link" danger size="small" onClick={() => handleDelete(record.id)}>
          删除
        </Button>
      ),
    },
  ]

  const tabItems = [
    { key: 'video', label: '视频' },
    { key: 'text', label: '文案' },
    { key: 'cover', label: '封面' },
    { key: 'topic', label: '话题' },
    { key: 'audio', label: '音频' },
  ]

  const typeLabels: Record<string, string> = {
    video: '视频',
    text: '文案',
    cover: '封面',
    topic: '话题',
    audio: '音频',
  }

  return (
    <>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ marginBottom: 16 }}
      />

      <Space style={{ marginBottom: 16 }}>
        <Upload
          accept={activeTab === 'video' ? 'video/*' : activeTab === 'audio' ? 'audio/*' : activeTab === 'cover' ? 'image/*' : '.txt'}
          showUploadList={false}
          customRequest={async ({ file, onSuccess }) => {
            try {
              const formData = new FormData()
              formData.append('file', file as File)
              await api.post(`/materials/upload/${activeTab}`, formData)
              message.success('上传成功')
              fetchMaterials()
              fetchFiles()
              onSuccess?.({})
            } catch (error) {
              message.error('上传失败')
            }
          }}
        >
          <Button icon={<UploadOutlined />}>上传{typeLabels[activeTab]}</Button>
        </Upload>
      </Space>

      <Space style={{ width: '100%' }} size="large">
        <Card title="素材库" style={{ flex: 1 }}>
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
          extra={<Button icon={<FolderOpenOutlined />} onClick={fetchFiles}>刷新</Button>}
          style={{ flex: 1, maxHeight: 500, overflow: 'auto' }}
        >
          <List
            size="small"
            dataSource={files[activeTab] || []}
            renderItem={(item: FileInfo) => (
              <List.Item>
                <Space>
                  <Text>{item.name}</Text>
                  <Text type="secondary">{((item.size || 0) / 1024 / 1024).toFixed(2)} MB</Text>
                </Space>
              </List.Item>
            )}
            locale={{ emptyText: '暂无文件' }}
          />
        </Card>
      </Space>
    </>
  )
}
