import { useEffect, useState, useCallback, type CSSProperties } from 'react'
import { Table, Button, Space, Tabs, Card, List, Typography, message, Upload, Row, Col, Modal, Form, Input, Select, Popconfirm } from 'antd'
import { UploadOutlined, SyncOutlined, ScanOutlined, FileOutlined, ShopOutlined, PlusOutlined, DeleteOutlined, LinkOutlined } from '@ant-design/icons'
import { useMaterials, useMaterialStats, useScanMaterials, useImportMaterials, useDeleteMaterial, useProducts, useCreateProduct, useDeleteProduct, useUpdateMaterial } from '../hooks'
import { api } from '../services/api'

const { Text } = Typography

interface Material {
  id: number
  type: string
  name?: string | null
  path?: string | null
  content?: string | null
  size?: number | null
  product_id?: number | null
  product_name?: string | null
  created_at: string
}

interface FileInfo {
  name: string
  path: string
  size: number
  type: string
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
  const [files, setFiles] = useState<FileInfo[]>([])
  const [activeTab, setActiveTab] = useState('video')
  const [productModalVisible, setProductModalVisible] = useState(false)
  const [productForm] = Form.useForm<{ name: string; link?: string }>()

  // 使用 React Query hooks
  const { data: materialsData, refetch: refetchMaterials } = useMaterials()
  const { data: stats, refetch: refetchStats } = useMaterialStats()
  const scanMaterials = useScanMaterials()
  const importMaterials = useImportMaterials()
  const deleteMaterial = useDeleteMaterial()
  const { data: products = [] } = useProducts()
  const createProduct = useCreateProduct()
  const deleteProduct = useDeleteProduct()
  const updateMaterial = useUpdateMaterial()

  // 规范化 materials 数据
  const materials = Array.isArray(materialsData) ? materialsData : []

  // 获取本地文件列表
  const fetchFiles = useCallback(async () => {
    try {
      const res = await api.get<{ files?: FileInfo[] }>(`/materials/path/${activeTab}`)
      setFiles(res.data.files || [])
    } catch (error: unknown) {
      if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('获取文件失败')
      }
    }
  }, [activeTab])

  // 当切换标签时刷新文件列表
  useEffect(() => {
    fetchFiles()
  }, [activeTab])

  const handleScan = async () => {
    try {
      const res = await scanMaterials.mutateAsync({ type: activeTab }) as { total?: number }
      message.success(`扫描完成，发现 ${res?.total || 0} 个文件`)
      fetchFiles()
    } catch (error) {
      message.error('扫描失败')
    }
  }

  const handleImport = async () => {
    try {
      const res = await importMaterials.mutateAsync({ type: activeTab }) as { success?: number; failed?: number }
      message.success(`导入完成: 成功 ${res?.success || 0}, 失败 ${res?.failed || 0}`)
      refetchMaterials()
      refetchStats()
    } catch (error) {
      message.error('导入失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMaterial.mutateAsync(id)
      message.success('删除成功')
      refetchMaterials()
      refetchStats()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleAddProduct = useCallback(async () => {
    try {
      const values = await productForm.validateFields()
      await createProduct.mutateAsync(values)
      message.success('添加商品成功')
      setProductModalVisible(false)
      productForm.resetFields()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      message.error('添加商品失败')
    }
  }, [productForm, createProduct])

  const handleDeleteProduct = useCallback(async (id: number) => {
    try {
      await deleteProduct.mutateAsync(id)
      message.success('删除商品成功')
    } catch (error) {
      message.error('删除商品失败')
    }
  }, [deleteProduct])

  const handleLinkProduct = useCallback(async (materialId: number, productId: number | undefined) => {
    try {
      await updateMaterial.mutateAsync({ materialId, data: { product_id: productId ?? null } as Record<string, unknown> })
      message.success('关联已更新')
      refetchMaterials()
    } catch (error) {
      message.error('关联失败')
    }
  }, [updateMaterial, refetchMaterials])

  const productOptions = products.map((p: { id: number; name: string }) => ({ label: p.name, value: p.id }))

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
      title: '关联商品',
      dataIndex: 'product_id',
      key: 'product_id',
      width: 150,
      render: (_: unknown, record: Material) => (
        <Select
          allowClear
          size="small"
          placeholder="选择商品"
          style={{ width: 130 }}
          value={record.product_id ?? undefined}
          options={productOptions}
          onChange={(val: number | undefined) => handleLinkProduct(record.id, val)}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: Material) => (
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
      {/* 商品管理 */}
      <Card
        title={<><ShopOutlined /> 商品管理</>}
        size="small"
        style={{ marginBottom: 16 }}
        extra={
          <Button size="small" icon={<PlusOutlined />} onClick={() => setProductModalVisible(true)}>
            添加商品
          </Button>
        }
      >
        <Space wrap>
          {products.map((p: { id: number; name: string; link?: string | null }) => (
            <Card key={p.id} size="small" style={{ width: 200 }}>
              <Space direction="vertical" size={2} style={{ width: '100%' }}>
                <Text strong>{p.name}</Text>
                {p.link && <Text type="secondary" style={{ fontSize: 12 }} ellipsis>{p.link}</Text>}
                <Popconfirm title="确定删除？" onConfirm={() => handleDeleteProduct(p.id)}>
                  <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
                </Popconfirm>
              </Space>
            </Card>
          ))}
          {products.length === 0 && <Text type="secondary">暂无商品，点击"添加商品"开始</Text>}
        </Space>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Card size="small">
            <Statistic title="视频" value={Number(stats?.video?.count) || 0} suffix={`(${formatSize(Number(stats?.video?.size) || 0)})`} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="文案" value={Number(stats?.text?.count) || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="封面" value={Number(stats?.cover?.count) || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="话题" value={Number(stats?.topic?.count) || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="音频" value={Number(stats?.audio?.count) || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card size="small">
            <Statistic title="总计" value={Number((stats as { total?: { count?: number } })?.total?.count) || 0} valueStyle={{ color: '#1890ff' }} />
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
              refetchMaterials()
              fetchFiles()
              refetchStats()
              onSuccess?.({})
            } catch (error) {
              message.error('上传失败')
            }
          }}
        >
          <Button icon={<UploadOutlined />}>上传{typeLabels[activeTab]}</Button>
        </Upload>

        <Button icon={<ScanOutlined />} onClick={handleScan} loading={scanMaterials.isPending}>
          扫描本地
        </Button>

        <Button icon={<SyncOutlined />} onClick={handleImport} loading={importMaterials.isPending}>
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
            loading={materialsData === undefined}
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

      {/* 添加商品 Modal */}
      <Modal
        title="添加商品"
        open={productModalVisible}
        onOk={handleAddProduct}
        confirmLoading={createProduct.isPending}
        onCancel={() => { setProductModalVisible(false); productForm.resetFields() }}
        destroyOnClose
      >
        <Form form={productForm} layout="vertical">
          <Form.Item name="name" label="商品名称" rules={[{ required: true, message: '请输入商品名称' }]}>
            <Input placeholder="请输入商品名称" />
          </Form.Item>
          <Form.Item name="link" label="商品链接">
            <Input placeholder="请输入得物商品链接" prefix={<LinkOutlined />} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

// 简单的统计组件
function Statistic({ title, value, suffix, valueStyle }: { title: string; value: number; suffix?: string; valueStyle?: CSSProperties }) {
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
