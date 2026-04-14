import { Button, Space, Table, Tag, Typography } from 'antd'

import type { AdminSessionResponse } from '../types'

interface SessionListProps {
  sessions: AdminSessionResponse[]
  onRevoke: (session: AdminSessionResponse) => void
  revokingSessionId?: number | null
}

const STATUS_COLOR: Record<string, string> = {
  authenticated_active: 'success',
  authenticated_grace: 'warning',
  refresh_required: 'warning',
  revoked: 'error',
  device_mismatch: 'error',
  expired: 'warning',
  unauthenticated: 'default',
  error: 'error',
  authorizing: 'processing',
}

export default function SessionList({
  sessions,
  onRevoke,
  revokingSessionId,
}: SessionListProps) {
  return (
    <Table<AdminSessionResponse>
      rowKey="session_id"
      dataSource={sessions}
      pagination={false}
      data-testid="auth-admin-session-list"
      columns={[
        {
          title: 'Session',
          key: 'session',
          render: (_, record) => (
            <Space direction="vertical" size={0}>
              <Typography.Text strong>
                {record.display_name ?? record.remote_user_id ?? `Session ${record.session_id}`}
              </Typography.Text>
              <Typography.Text type="secondary">
                {record.remote_user_id ?? 'No remote user'} · {record.device_id ?? 'No device'}
              </Typography.Text>
            </Space>
          ),
        },
        {
          title: 'State',
          dataIndex: 'auth_state',
          key: 'auth_state',
          render: (value: string) => <Tag color={STATUS_COLOR[value] ?? 'default'}>{value}</Tag>,
        },
        {
          title: 'Secrets',
          key: 'secrets',
          render: (_, record) => (
            <Space>
              <Tag color={record.has_access_token ? 'success' : 'default'}>Access</Tag>
              <Tag color={record.has_refresh_token ? 'success' : 'default'}>Refresh</Tag>
            </Space>
          ),
        },
        {
          title: 'Current',
          key: 'current',
          render: (_, record) =>
            record.is_current_session ? <Tag color="blue">Current session</Tag> : <Tag>Historical</Tag>,
        },
        {
          title: 'Action',
          key: 'action',
          render: (_, record) => (
            <Button
              danger
              size="small"
              onClick={() => onRevoke(record)}
              loading={revokingSessionId === record.session_id}
              disabled={record.auth_state === 'revoked'}
            >
              Revoke
            </Button>
          ),
        },
      ]}
    />
  )
}
