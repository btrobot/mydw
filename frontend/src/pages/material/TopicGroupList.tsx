import { useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Space, Modal, Form, Input, Select, Popconfirm, message } from 'antd'
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'

import {
  useTopics,
  useCreateTopicGroup,
  useUpdateTopicGroup,
  useDeleteTopicGroup,
} from '@/hooks'
import type { TopicGroupResponse, TopicGroupListResponse, TopicResponse } from '@/types/material'
import { handleApiError } from '@/utils/error'
import { api } from '@/services/api'

interface GroupFormValues {
  name: string
  topic_ids: number[]
}

export default function TopicGroupList() {
  const navigate = useNavigate()
  const actionRef = useRef<ActionType>()

  const [modalOpen, setModalOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<TopicGroupResponse | null>(null)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [form] = Form.useForm<GroupFormValues>()

  const { data: allTopics = [] } = useTopics()
  const createTopicGroup = useCreateTopicGroup()
  const updateTopicGroup = useUpdateTopicGroup()
  const deleteTopicGroup = useDeleteTopicGroup()

  const topicOptions = allTopics.map((t: TopicResponse) => ({ label: t.name, value: t.id }))

  const handleOpenCreate = useCallback(() => {
    setEditingGroup(null)
    form.resetFields()
    setModalOpen(true)
  }, [form])

  const handleOpenEdit = useCallback((group: TopicGroupResponse) => {
    setEditingGroup(group)
    form.setFieldsValue({ name: group.name, topic_ids: group.topic_ids })
    setModalOpen(true)
  }, [form])

  const handleSave = useCallback(async () => {
    try {
      const values = await form.validateFields()
      if (editingGroup) {
        await updateTopicGroup.mutateAsync({ id: editingGroup.id, payload: values })
        message.success('话题组更新成功')
      } else {
        await createTopicGroup.mutateAsync(values)
        message.success('话题组创建成功')
      }
      setModalOpen(false)
      form.resetFields()
      setEditingGroup(null)
      actionRef.current?.reload()
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) return
      handleApiError(error, editingGroup ? '更新话题组失败' : '创建话题组失败')
    }
  }, [form, editingGroup, createTopicGroup, updateTopicGroup])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await deleteTopicGroup.mutateAsync(id)
      message.success('删除成功')
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '删除话题组失败')
    }
  }, [deleteTopicGroup])

  const handleBatchDelete = useCallback(async () => {
    try {
      await Promise.all(selectedIds.map((id) => deleteTopicGroup.mutateAsync(id)))
      setSelectedIds([])
      message.success(`已删除 ${selectedIds.length} 个话题组`)
      actionRef.current?.reload()
    } catch (error: unknown) {
      handleApiError(error, '批量删除失败')
    }
  }, [selectedIds, deleteTopicGroup])

  const handleView = useCallback((id: number) => {
    navigate(`/material/topic-group/${id}`)
  }, [navigate])

  const columns: ProColumns<TopicGroupResponse>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 70,
      hideInSearch: true,
    },
    {
      title: '名称',
      dataIndex: 'name',
      ellipsis: true,
    },
    {
      title: '话题数量',
      dataIndex: 'topic_ids',
      width: 100,
      hideInSearch: true,
      render: (_, record) => record.topic_ids.length,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      hideInSearch: true,
      render: (_, record) => new Date(record.created_at).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      hideInSearch: true,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleView(record.id)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm title="确定删除该话题组？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const isSaving = createTopicGroup.isPending || updateTopicGroup.isPending

  return (
    <>
      <ProTable<TopicGroupResponse>
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        request={async (params) => {
          const { data } = await api.get<TopicGroupListResponse>('/topic-groups', {
            params: params.name ? { keyword: params.name } : undefined,
          })
          return { data: data.items, success: true, total: data.items.length }
        }}
        rowSelection={{
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        }}
        tableAlertOptionRender={() => (
          <Popconfirm title={`确定删除 ${selectedIds.length} 项？`} onConfirm={handleBatchDelete}>
            <Button danger size="small" icon={<DeleteOutlined />} loading={deleteTopicGroup.isPending}>
              批量删除 ({selectedIds.length})
            </Button>
          </Popconfirm>
        )}
        toolBarRender={() => [
          <Button
            key="add"
            icon={<PlusOutlined />}
            onClick={handleOpenCreate}
          >
            新建话题组
          </Button>,
        ]}
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 条` }}
        size="small"
        search={{ labelWidth: 'auto' }}
      />

      <Modal
        title={editingGroup ? '编辑话题组' : '新建话题组'}
        open={modalOpen}
        onOk={handleSave}
        confirmLoading={isSaving}
        onCancel={() => { setModalOpen(false); form.resetFields(); setEditingGroup(null) }}
        destroyOnHidden
        width={520}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="组名"
            rules={[{ required: true, message: '请输入话题组名称' }]}
          >
            <Input placeholder="话题组名称" />
          </Form.Item>
          <Form.Item
            name="topic_ids"
            label="选择话题"
            rules={[{ required: true, message: '请至少选择一个话题' }]}
          >
            <Select
              mode="multiple"
              placeholder="从话题库中选择话题（可多选）"
              options={topicOptions}
              filterOption={(input, option) =>
                (option?.label as string ?? '').toLowerCase().includes(input.toLowerCase())
              }
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
