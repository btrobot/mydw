import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  Flex,
  Form,
  Input,
  InputNumber,
  List,
  Space,
  Tag,
  Typography,
} from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { OffsetPaginationControls } from '../../components/pagination/OffsetPaginationControls.js';
import { EmptyState } from '../../components/states/EmptyState.js';
import { ErrorState } from '../../components/states/ErrorState.js';
import { LoadingState } from '../../components/states/LoadingState.js';
import {
  AdminApiError,
  buildAuditLogQuery,
  getAdminAuditLogs,
  isAuthExpiredError,
  type AdminAuditFilters,
  type AdminAuditRecord,
  type OffsetPaginationFilters,
} from '../../features/auth/auth-client.js';
import { useAuth } from '../../features/auth/auth-context.js';

const DEFAULT_FILTERS: AdminAuditFilters = {
  eventType: '',
  actorId: '',
  targetUserId: '',
  targetDeviceId: '',
  targetSessionId: '',
  createdFrom: '',
  createdTo: '',
  limit: 50,
  offset: 0,
};

const HIGHLIGHTED_DETAIL_KEYS = ['reason', 'required_permission', 'user_id', 'device_id', 'session_id'];

function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return 'n/a';
  return String(value);
}

function formatAuditValue(value: unknown): string {
  if (value === null || value === undefined) return 'n/a';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return JSON.stringify(value);
}

function renderAuditTags(record: AdminAuditRecord): JSX.Element {
  return (
    <Space wrap size={[8, 8]}>
      <Tag>actor:{record.actor_id ?? 'n/a'}</Tag>
      <Tag>user:{record.target_user_id ?? 'n/a'}</Tag>
      <Tag>device:{record.target_device_id ?? 'n/a'}</Tag>
      <Tag>session:{record.target_session_id ?? 'n/a'}</Tag>
    </Space>
  );
}

export function AuditLogsPage(): JSX.Element {
  const navigate = useNavigate();
  const { accessToken, handleExpiredSession } = useAuth();
  const [draftFilters, setDraftFilters] = useState<AdminAuditFilters>(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<AdminAuditFilters>(DEFAULT_FILTERS);
  const [selectedAuditId, setSelectedAuditId] = useState<string | null>(null);

  const auditQuery = useQuery({
    queryKey: ['adminAuditLogs', appliedFilters],
    queryFn: () => getAdminAuditLogs(accessToken ?? '', appliedFilters),
    enabled: Boolean(accessToken),
  });

  const selectedAudit = useMemo(
    () => auditQuery.data?.items.find((item) => item.id === selectedAuditId) ?? null,
    [auditQuery.data?.items, selectedAuditId]
  );

  useEffect(() => {
    if (auditQuery.error instanceof AdminApiError && isAuthExpiredError(auditQuery.error.errorCode)) {
      handleExpiredSession();
      navigate('/login', { replace: true, state: { from: '/audit-logs' } });
    }
  }, [auditQuery.error, handleExpiredSession, navigate]);

  useEffect(() => {
    const items = auditQuery.data?.items ?? [];
    if (items.length === 0) {
      setSelectedAuditId(null);
      return;
    }

    if (!selectedAuditId || !items.some((item) => item.id === selectedAuditId)) {
      setSelectedAuditId(items[0].id);
    }
  }, [auditQuery.data?.items, selectedAuditId]);

  function applyFilters(nextFilters: AdminAuditFilters): void {
    setSelectedAuditId(null);
    setDraftFilters(nextFilters);
    setAppliedFilters(nextFilters);
  }

  function applyPagination(nextPagination: OffsetPaginationFilters): void {
    setSelectedAuditId(null);
    setDraftFilters((current) => ({
      ...current,
      ...nextPagination,
    }));
    setAppliedFilters((current) => ({
      ...current,
      ...nextPagination,
    }));
  }

  if (!accessToken) {
    return <ErrorState title="Admin session missing" description="Please sign in again before loading audit logs." />;
  }

  if (auditQuery.isLoading && !auditQuery.data) {
    return <LoadingState title="Loading audit logs" />;
  }

  const highlightedEntries = selectedAudit
    ? Object.entries(selectedAudit.details).filter(([key]) => HIGHLIGHTED_DETAIL_KEYS.includes(key))
    : [];
  const remainingEntries = selectedAudit
    ? Object.entries(selectedAudit.details).filter(([key]) => !HIGHLIGHTED_DETAIL_KEYS.includes(key))
    : [];
  const queryPreview = buildAuditLogQuery(appliedFilters);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={2} style={{ marginBottom: 8 }}>
          Audit logs
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Day 3.4 migrates the read-only audit investigation route into React with stable filter ordering, UTC-safe time
          boundaries, and list-derived detail inspection.
        </Typography.Paragraph>
      </div>

      <Alert
        type="info"
        showIcon
        message="Read-only investigation route"
        description="Audit logs stay backend-driven: filters query the existing admin API, selection is derived from the current page, and no optimistic local state is introduced."
      />

      <Card>
        <Form
          layout="vertical"
          onFinish={() => {
            applyFilters({
              ...draftFilters,
              limit: Math.min(200, Math.max(1, draftFilters.limit)),
              offset: Math.max(0, draftFilters.offset),
            });
          }}
        >
          <Flex gap={16} wrap="wrap" align="end">
            <Form.Item label="Event type" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
              <Input
                value={draftFilters.eventType}
                placeholder="authorization_user_revoked"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    eventType: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Actor id" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
              <Input
                value={draftFilters.actorId}
                placeholder="admin_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    actorId: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Target user" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
              <Input
                value={draftFilters.targetUserId}
                placeholder="u_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    targetUserId: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Target device" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
              <Input
                value={draftFilters.targetDeviceId}
                placeholder="device_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    targetDeviceId: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Target session" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
              <Input
                value={draftFilters.targetSessionId}
                placeholder="sess_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    targetSessionId: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Created from" style={{ minWidth: 220, marginBottom: 0 }}>
              <Input
                type="datetime-local"
                value={draftFilters.createdFrom}
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    createdFrom: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Created to" style={{ minWidth: 220, marginBottom: 0 }}>
              <Input
                type="datetime-local"
                value={draftFilters.createdTo}
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    createdTo: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Offset" style={{ minWidth: 120, marginBottom: 0 }}>
              <InputNumber
                min={0}
                value={draftFilters.offset}
                style={{ width: '100%' }}
                onChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    offset: typeof value === 'number' ? value : current.offset,
                  }))
                }
              />
            </Form.Item>
            <Space wrap>
              <Button type="primary" htmlType="submit" loading={auditQuery.isFetching}>
                Refresh audit logs
              </Button>
              <Button onClick={() => applyFilters(DEFAULT_FILTERS)}>Clear filters</Button>
            </Space>
          </Flex>
        </Form>
      </Card>

      <Flex gap={16} align="stretch" wrap="wrap">
        <Card title={`Audit events (${auditQuery.data?.total ?? 0})`} style={{ flex: '1 1 420px', minWidth: 340 }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <OffsetPaginationControls
              filters={appliedFilters}
              response={auditQuery.data}
              loading={auditQuery.isFetching}
              summarySuffix={`showing ${auditQuery.data?.items.length ?? 0} records from offset ${appliedFilters.offset}`}
              onChange={applyPagination}
            />
            <code data-testid="audit-query-preview" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {queryPreview}
            </code>

            {auditQuery.isError ? (
              <ErrorState
                title="Audit logs unavailable"
                description="The React audit investigation list could not be loaded from the admin API."
                retryLabel="Retry audit logs"
                onRetry={() => void auditQuery.refetch()}
              />
            ) : auditQuery.data && auditQuery.data.items.length > 0 ? (
              <List
                dataSource={auditQuery.data.items}
                renderItem={(item) => (
                  <List.Item
                    key={item.id}
                    style={{
                      cursor: 'pointer',
                      paddingInline: 12,
                      borderRadius: 8,
                      background: item.id === selectedAuditId ? '#f0f5ff' : undefined,
                      border: item.id === selectedAuditId ? '1px solid #adc6ff' : '1px solid transparent',
                      marginBottom: 8,
                    }}
                    onClick={() => setSelectedAuditId(item.id)}
                  >
                    <List.Item.Meta
                      title={
                        <Space direction="vertical" size={4}>
                          <Space wrap>
                            <Typography.Text strong>{item.event_type}</Typography.Text>
                            <Tag>{item.actor_type ?? 'unknown-actor'}</Tag>
                          </Space>
                          {renderAuditTags(item)}
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size={4}>
                          <Typography.Text type="secondary">{item.created_at}</Typography.Text>
                          <Typography.Text type="secondary">request: {item.request_id ?? 'n/a'}</Typography.Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : auditQuery.isFetching ? (
              <LoadingState title="Refreshing audit logs" />
            ) : (
              <EmptyState description="No audit events matched the current filters." />
            )}
          </Space>
        </Card>

        <Card title="Selected event" style={{ flex: '2 1 560px', minWidth: 360 }}>
          {selectedAudit ? (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Descriptions bordered column={2} size="small">
                <Descriptions.Item label="Event type">{selectedAudit.event_type}</Descriptions.Item>
                <Descriptions.Item label="Created at">{selectedAudit.created_at}</Descriptions.Item>
                <Descriptions.Item label="Actor type">{formatValue(selectedAudit.actor_type)}</Descriptions.Item>
                <Descriptions.Item label="Actor id">{formatValue(selectedAudit.actor_id)}</Descriptions.Item>
                <Descriptions.Item label="Target user">{formatValue(selectedAudit.target_user_id)}</Descriptions.Item>
                <Descriptions.Item label="Target device">{formatValue(selectedAudit.target_device_id)}</Descriptions.Item>
                <Descriptions.Item label="Target session">{formatValue(selectedAudit.target_session_id)}</Descriptions.Item>
                <Descriptions.Item label="Request ID">{formatValue(selectedAudit.request_id)}</Descriptions.Item>
                <Descriptions.Item label="Trace ID" span={2}>
                  {formatValue(selectedAudit.trace_id)}
                </Descriptions.Item>
              </Descriptions>

              {renderAuditTags(selectedAudit)}

              {highlightedEntries.length > 0 ? (
                <Card size="small" title="Highlighted detail fields">
                  <Descriptions column={1} size="small">
                    {highlightedEntries.map(([key, value]) => (
                      <Descriptions.Item key={key} label={key}>
                        {formatAuditValue(value)}
                      </Descriptions.Item>
                    ))}
                  </Descriptions>
                </Card>
              ) : null}

              {remainingEntries.length > 0 ? (
                <Card size="small" title="Remaining detail payload">
                  <pre data-testid="audit-detail-json" style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {JSON.stringify(Object.fromEntries(remainingEntries), null, 2)}
                  </pre>
                </Card>
              ) : (
                <Alert
                  type="info"
                  showIcon
                  message="No additional detail payload"
                  description="This audit event did not include any remaining structured fields beyond the highlighted keys."
                />
              )}
            </Space>
          ) : auditQuery.isFetching ? (
            <LoadingState title="Refreshing audit detail" />
          ) : selectedAuditId ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select an audit event to inspect detail." />
          ) : (
            <EmptyState description="Choose an audit event from the list to inspect request tracing and normalized details." />
          )}
        </Card>
      </Flex>
    </Space>
  );
}
