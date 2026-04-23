import { ArrowRightOutlined } from '@ant-design/icons'
import { ProTable } from '@ant-design/pro-components'
import type { ProColumns, ProFormInstance } from '@ant-design/pro-components'
import { Button, Select, Space, Tag, Typography } from 'antd'
import { useMemo } from 'react'
import type { MutableRefObject, ReactNode } from 'react'

import { countEnabledCreativeInputItems, formatCreativeDuration } from '../../creativeAuthoring'
import {
  creativeStatusMeta,
  creativeWorkbenchPoolStateMeta,
  formatCreativeTimestamp,
} from '../../types/creative'
import type {
  WorkbenchFormValues,
  WorkbenchSortKind,
  WorkbenchTableRow,
  WorkbenchQueryState,
} from './shared'

const { Text } = Typography

const creativeStatusValueEnum = Object.fromEntries(
  Object.entries(creativeStatusMeta).map(([key, value]) => [key, { text: value.label }]),
)

const creativePoolValueEnum = Object.fromEntries(
  Object.entries(creativeWorkbenchPoolStateMeta).map(([key, value]) => [key, { text: value.label }]),
) as Record<WorkbenchTableRow['poolState'], { text: string }>

const workbenchSortOptions: Array<{ label: string; value: WorkbenchSortKind }> = [
  { label: '最近更新优先', value: 'updated_desc' },
  { label: '最早更新优先', value: 'updated_asc' },
  { label: '待处理优先', value: 'attention_desc' },
  { label: '最近失败优先', value: 'failed_desc' },
]

type WorkbenchTableProps = {
  appliedFormValues: WorkbenchFormValues
  appliedQueryState: WorkbenchQueryState
  createPending: boolean
  dataSource: WorkbenchTableRow[]
  emptyState: ReactNode
  formRef: MutableRefObject<ProFormInstance<WorkbenchFormValues> | undefined>
  loading: boolean
  presetBar: ReactNode
  total: number
  onApplyFilters: (values: WorkbenchFormValues) => void
  onCreateCreative: () => void
  onOpenDashboard: () => void
  onOpenCreativeDetail: (creativeId: number, options?: { tool?: 'ai-clip' }) => void
  onPaginationChange: (page: number, pageSize: number) => void
  onResetFilters: () => void
  onSortChange: (sort: WorkbenchSortKind) => void
}

export default function WorkbenchTable({
  appliedFormValues,
  appliedQueryState,
  createPending,
  dataSource,
  emptyState,
  formRef,
  loading,
  presetBar,
  total,
  onApplyFilters,
  onCreateCreative,
  onOpenDashboard,
  onOpenCreativeDetail,
  onPaginationChange,
  onResetFilters,
  onSortChange,
}: WorkbenchTableProps) {
  const columns = useMemo<ProColumns<WorkbenchTableRow>[]>(() => [
    {
      title: '作品检索',
      dataIndex: 'keyword',
      hideInTable: true,
      fieldProps: {
        placeholder: '按标题或作品编号搜索',
        allowClear: true,
        'data-testid': 'creative-workbench-search-input',
      },
    },
    {
      title: '作品编号',
      dataIndex: 'creative_no',
      width: 160,
      hideInSearch: true,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          <Text strong>{record.creative_no}</Text>
          <Text type="secondary">#{record.id}</Text>
        </Space>
      ),
    },
    {
      title: '作品 / 创作定义',
      dataIndex: 'title',
      ellipsis: true,
      hideInSearch: true,
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          <Text strong>{record.title?.trim() || record.creative_no}</Text>
          <Text type="secondary">
            {[
              record.subject_product_name_snapshot || undefined,
              formatCreativeDuration(record.target_duration_seconds),
              `${countEnabledCreativeInputItems(record.input_items)} 个编排项`,
            ]
              .filter(Boolean)
              .join(' · ')}
          </Text>
          {record.main_copywriting_text?.trim() ? (
            <Text type="secondary" ellipsis={{ tooltip: record.main_copywriting_text }}>
              主文案：{record.main_copywriting_text}
            </Text>
          ) : null}
          {record.generation_error_msg ? (
            <Text type="warning">最近一次生成回填失败</Text>
          ) : (
            <Text type="secondary">当前版本 #{record.current_version_id ?? '-'}</Text>
          )}
        </Space>
      ),
    },
    {
      title: '作品状态',
      dataIndex: 'status',
      width: 140,
      valueType: 'select',
      valueEnum: creativeStatusValueEnum,
      fieldProps: {
        placeholder: '按作品状态筛选',
        allowClear: true,
        'data-testid': 'creative-workbench-status-filter',
      },
      render: (_, record) => {
        const statusMeta = creativeStatusMeta[record.status]
        return <Tag color={statusMeta.color}>{statusMeta.label}</Tag>
      },
    },
    {
      title: '发布准备',
      dataIndex: 'poolState',
      width: 220,
      valueType: 'select',
      valueEnum: creativePoolValueEnum,
      fieldProps: {
        placeholder: '按发布准备筛选',
        allowClear: true,
        'data-testid': 'creative-workbench-pool-filter',
      },
      render: (_, record) => (
        <Space direction="vertical" size={4} data-testid={`creative-workbench-pool-state-${record.id}`}>
          <Space wrap size={[4, 4]}>
            <Tag color={creativeWorkbenchPoolStateMeta[record.poolState].color}>
              {creativeWorkbenchPoolStateMeta[record.poolState].label}
            </Tag>
            {record.active_pool_version_id ? (
              <Tag color={record.poolAligned ? 'success' : 'warning'}>
                池版本 #{record.active_pool_version_id}
              </Tag>
            ) : null}
          </Space>
          <Text type="secondary">
            {record.active_pool_item_id ? `发布池记录 #${record.active_pool_item_id}` : '当前版本尚未进入发布池'}
          </Text>
        </Space>
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      width: 180,
      hideInSearch: true,
      render: (_, record) => formatCreativeTimestamp(record.updated_at),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      hideInSearch: true,
      render: (_, record) => (
        <Space size={0} wrap>
          <Button
            type="link"
            onClick={() => onOpenCreativeDetail(record.id)}
            data-testid={`creative-workbench-open-detail-${record.id}`}
          >
            查看作品
          </Button>
          <Button
            type="link"
            onClick={() => onOpenCreativeDetail(record.id)}
            disabled={!record.current_version_id}
            data-testid={`creative-workbench-open-review-${record.id}`}
          >
            审核当前版本
          </Button>
          <Button
            type="link"
            icon={<ArrowRightOutlined />}
            onClick={() => onOpenCreativeDetail(record.id, { tool: 'ai-clip' })}
            disabled={!record.current_version_id}
            data-testid={`creative-workbench-ai-clip-${record.id}`}
          >
            进入 AIClip
          </Button>
        </Space>
      ),
    },
  ], [onOpenCreativeDetail])

  return (
    <ProTable<WorkbenchTableRow, WorkbenchFormValues>
      formRef={formRef}
      rowKey="id"
      columns={columns}
      cardBordered
      headerTitle="待处理作品"
      options={{ density: false, setting: false }}
      dataSource={dataSource}
      loading={loading}
      pagination={{
        current: appliedQueryState.page,
        pageSize: appliedQueryState.pageSize,
        total,
        showSizeChanger: true,
        showTotal: (count) => `共 ${count} 条作品`,
        onChange: onPaginationChange,
      }}
      form={{
        initialValues: appliedFormValues,
      }}
      search={{
        labelWidth: 'auto',
        defaultCollapsed: false,
        searchText: '应用筛选',
        resetText: '重置筛选',
      }}
      onSubmit={onApplyFilters}
      onReset={onResetFilters}
      tableExtraRender={() => presetBar}
      locale={{
        emptyText: emptyState,
      }}
      toolBarRender={() => [
        <div key="sort" data-testid="creative-workbench-sort-select">
          <Select
            value={appliedQueryState.sort}
            options={workbenchSortOptions}
            style={{ width: 180 }}
            onChange={(value) => onSortChange(value)}
          />
        </div>,
        <Button
          key="create"
          type="primary"
          loading={createPending}
          onClick={onCreateCreative}
          data-testid="creative-workbench-create"
        >
          新建作品
        </Button>,
        <Button
          key="dashboard"
          onClick={onOpenDashboard}
          data-testid="creative-workbench-open-dashboard"
        >
          运行总览
        </Button>,
      ]}
    />
  )
}
