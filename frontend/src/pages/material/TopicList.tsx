import { useState, useCallback } from 'react'
import {
  Table, Button, Space, Typography, message,
  Modal, Form, Input, InputNumber, Select, Popconfirm, Card, Tag, Empty,
} from 'antd'
import {
  PlusOutlined, SearchOutlined, GlobalOutlined,
} from '@ant-design/icons'

import {
  useTopics, useCreateTopic, useDeleteTopic, useSearchTopics,
  useGlobalTopics, useSetGlobalTopics, useBatchDeleteTopics,
} from '@/hooks'
import type { TopicResponse } from '@/types/material'
import { handleApiError } from '@/utils/error'
import ListPageLayout from '@/components/ListPageLayout'
import BatchDeleteButton from '@/components/BatchDeleteButton'

const { Text } = Typography

interface TopicFormValues {
  name: string
  heat?: number
}

export default function TopicList() {
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [globalModalOpen, setGlobalModalOpen] = useState(false)
  const [searchModalOpen, setSearchModalOpen] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [searchInput, setSearchInput] = useState<string>('')
  const [filterKeyword, setFilterKeyword] = useState<string>('')
  const [filterSource, setFilterSource] = useState<string | undefined>(undefined)
  const [selectedGlobalIds, setSelectedGlobalIds] = useState<number[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<TopicFormValues>()

  const { data: topics = [], isLoading } = useTopics({
    keyword: filterKeyword || undefined,
    source: filterSource,
  })
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
    try {
      const result = await batchDeleteTopics.mutateAsync(selectedIds)
      setSelectedIds([])
      message.success(`已删除 ${result.deleted} 个话题${result.skipped > 0 ? `，${result.skipped} 项被跳过` : ''}`)
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, batchDeleteTopics])

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70, sorter: (a: TopicResponse, b: TopicResponse) => a.id - b.id },
    { title: '话题名称', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: '热度',
      dataIndex: 'heat',
      key: 'heat',
      width: 80,
      render: (v: number) => v.toLocaleString(),
      sorter: (a: TopicResponse, b: TopicResponse) => a.heat - b.heat,
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
      sorter: (a: TopicResponse, b: TopicResponse) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
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

      <ListPageLayout
        filterBar={
          <Space>
            <Input
              allowClear
              style={{ width: 200 }}
              placeholder="搜索话题名称"
              value={filterKeyword}
              onChange={(e) => setFilterKeyword(e.target.value)}
            />
            <Select
              allowClear
              style={{ width: 140 }}
              placeholder="来源"
              value={filterSource}
              onChange={(v) => setFilterSource(v)}
              options={[
                { label: '手动', value: 'manual' },
                { label: '搜索', value: 'search' },
              ]}
            />
          </Space>
        }
        actionBar={
          <Space>
            <Button icon={<SearchOutlined />} onClick={() => setSearchModalOpen(true)}>
              搜索得物话题
            </Button>
            <Button icon={<PlusOutlined />} onClick={() => setAddModalOpen(true)}>
              添加话题
            </Button>
            <BatchDeleteButton
              count={selectedIds.length}
              onConfirm={handleBatchDelete}
              loading={batchDeleteTopics.isPending}
            />
          </Space>
        }
      >
        <Table<TopicResponse>
          dataSource={topics}
          rowKey="id"
          columns={columns}
          loading={isLoading}
          pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
          size="small"
          rowSelection={{ selectedRowKeys: selectedIds, onChange: (keys) => setSelectedIds(keys as number[]) }}
        />
      </ListPageLayout>

      {/* 搜索得物话题 Modal */}
      <Modal
        title={<><SearchOutlined /> 搜索得物话题</>}
        open={searchModalOpen}
        onCancel={() => { setSearchModalOpen(false); setSearchKeyword(''); setSearchInput('') }}
        footer={null}
        destroyOnClose
        width={560}
      >
        <Space style={{ marginBottom: 12 }}>
          <Input
            placeholder="输入关键词搜索话题"
            style={{ width: 280 }}
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
                  <Text type="secondary" style={{ fontSize: 12 }}>已自动入库</Text>
                </Space>
              ))}
            </Space>
          )
        )}
      </Modal>

      {/* 添加话题 Modal */}
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
            <InputNumber placeholder="0" style={{ width: '100%' }} min={0} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 设置全局话题 Modal */}
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
