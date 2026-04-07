import { useState, useCallback } from 'react'
import {
  Table, Button, Space, Typography, message,
  Modal, Form, Input, Select, Popconfirm, Card, Tag, Empty,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, SearchOutlined, GlobalOutlined,
} from '@ant-design/icons'

import {
  useTopics, useCreateTopic, useDeleteTopic, useSearchTopics,
  useGlobalTopics, useSetGlobalTopics, useBatchDeleteTopics,
} from '@/hooks'
import type { TopicResponse } from '@/types/material'
import { handleApiError } from '@/utils/error'

const { Text } = Typography

interface TopicFormValues {
  name: string
  heat?: number
}

export default function TopicList() {
  const [sort, setSort] = useState<string>('created_at')
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [globalModalOpen, setGlobalModalOpen] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [searchInput, setSearchInput] = useState<string>('')
  const [selectedGlobalIds, setSelectedGlobalIds] = useState<number[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<TopicFormValues>()

  const { data: topics = [], isLoading } = useTopics(sort)
  const { data: searchResults = [], isFetching: isSearching } = useSearchTopics(searchKeyword)
  const { data: globalTopicsData } = useGlobalTopics()
  const createTopic = useCreateTopic()
  const deleteTopic = useDeleteTopic()
  const setGlobalTopics = useSetGlobalTopics()
  const batchDeleteTopics = useBatchDeleteTopics()

  const globalTopics = globalTopicsData?.topics ?? []
  const topicOptions = topics.map((t: TopicResponse) => ({ label: t.name, value: t.id }))

  const handleSearch = useCallback(() => {
    setSearchKeyword(searchInput.trim())
  }, [searchInput])

  const handleAddFromSearch = useCallback(async (topic: TopicResponse) => {
    message.success(`话题「${topic.name}」已在话题库中`)
  }, [])

  const handleOpenGlobalModal = useCallback(() => {
    setSelectedGlobalIds(globalTopicsData?.topic_ids ?? [])
    setGlobalModalOpen(true)
  }, [globalTopicsData])

  const handleSaveGlobalTopics = useCallback(async () => {
    try {
      await setGlobalTopics.mutateAsync({ topic_ids: selectedGlobalIds })
      message.success('全局话题设置成功')
      setGlobalModalOpen(false)
    } catch (error: unknown) {
      handleApiError(error, '设置全局话题失败')
    }
  }, [setGlobalTopics, selectedGlobalIds])

  const handleAdd = useCallback(async () => {
    try {
      const values = await form.validateFields()
      await createTopic.mutateAsync(values)
      message.success('添加话题成功')
      setAddModalOpen(false)
      form.resetFields()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      handleApiError(error, '添加话题失败')
    }
  }, [form, createTopic])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTopic.mutateAsync(id)
      message.success('删除成功')
    } catch (error: unknown) {
      handleApiError(error, '删除话题失败')
    }
  }, [deleteTopic])

  const handleBatchDelete = useCallback(async () => {
    const result = await batchDeleteTopics.mutateAsync(selectedIds)
    setSelectedIds([])
    message.success(`已删除 ${result.deleted} 个话题${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
  }, [selectedIds, batchDeleteTopics])

  const columns = [
    { title: '话题名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: '热度',
      dataIndex: 'heat',
      key: 'heat',
      width: 80,
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 80,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: TopicResponse) => (
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <Card size="small" style={{ marginBottom: 12 }} title={<><SearchOutlined /> 搜索话题</>}>
        <Space style={{ marginBottom: 8 }}>
          <Input
            placeholder="输入关键词搜索话题"
            style={{ width: 240 }}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onPressEnter={handleSearch}
            allowClear
            onClear={() => { setSearchKeyword(''); setSearchInput('') }}
          />
          <Button icon={<SearchOutlined />} onClick={handleSearch} loading={isSearching}>
            搜索
          </Button>
        </Space>
        {searchKeyword && (
          isSearching ? (
            <Text type="secondary">搜索中…</Text>
          ) : searchResults.length === 0 ? (
            <Empty description="未找到相关话题" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <Space wrap>
              {searchResults.map((t: TopicResponse) => (
                <Space key={t.id} size={4}>
                  <Tag color="blue">{t.name}</Tag>
                  <Tag color="orange">{t.heat.toLocaleString()}</Tag>
                  <Button size="small" type="link" onClick={() => handleAddFromSearch(t)}>
                    添加
                  </Button>
                </Space>
              ))}
            </Space>
          )
        )}
      </Card>

      <Card
        size="small"
        style={{ marginBottom: 12 }}
        title={<><GlobalOutlined /> 全局话题</>}
        extra={
          <Button size="small" icon={<GlobalOutlined />} onClick={handleOpenGlobalModal}>
            设置全局话题
          </Button>
        }
      >
        {globalTopics.length === 0 ? (
          <Empty description="暂未设置全局话题" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Space wrap>
            {globalTopics.map((t: TopicResponse) => (
              <Tag key={t.id} color="geekblue">{t.name}</Tag>
            ))}
          </Space>
        )}
      </Card>

      <Space style={{ marginBottom: 12 }}>
        <Select
          value={sort}
          onChange={setSort}
          style={{ width: 120 }}
          options={[
            { label: '最新', value: 'created_at' },
            { label: '热度', value: 'heat' },
          ]}
        />
        <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
          添加话题
        </Button>
        {selectedIds.length > 0 && (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger icon={<DeleteOutlined />}>批量删除 ({selectedIds.length})</Button>
          </Popconfirm>
        )}
      </Space>

      <Table<TopicResponse>
        dataSource={topics}
        rowKey="id"
        columns={columns}
        loading={isLoading}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
      />

      <Modal
        title="添加话题"
        open={addModalOpen}
        onOk={handleAdd}
        confirmLoading={createTopic.isPending}
        onCancel={() => { setAddModalOpen(false); form.resetFields() }}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="话题名称" rules={[{ required: true, message: '请输入话题名称' }]}>
            <Input placeholder="话题名称" />
          </Form.Item>
          <Form.Item name="heat" label="热度">
            <Input type="number" placeholder="0" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="设置全局话题"
        open={globalModalOpen}
        onOk={handleSaveGlobalTopics}
        confirmLoading={setGlobalTopics.isPending}
        onCancel={() => setGlobalModalOpen(false)}
        destroyOnClose
        width={520}
      >
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          从话题库中选择话题作为全局默认话题，发布时自动附加。
        </Text>
        <Select
          mode="multiple"
          style={{ width: '100%' }}
          placeholder="选择话题（可多选）"
          options={topicOptions}
          value={selectedGlobalIds}
          onChange={setSelectedGlobalIds}
          filterOption={(input, option) =>
            (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
          }
        />
      </Modal>
    </>
  )
}
