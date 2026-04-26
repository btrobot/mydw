import { useMutation, useQuery } from '@tanstack/react-query';
import { Alert, Button, Card, Descriptions, Empty, Flex, Form, Input, List, Select, Space, Tag, Typography } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { OffsetPaginationControls } from '../../components/pagination/OffsetPaginationControls.js';
import { EmptyState } from '../../components/states/EmptyState.js';
import { ErrorState } from '../../components/states/ErrorState.js';
import { LoadingState } from '../../components/states/LoadingState.js';
import {
  formatAdminListError,
  formatAdminMissingSession,
  formatFilteredEmptyState,
  formatSelectionEmptyState,
} from '../../components/states/adminCopy.js';
import {
  ADMIN_STEP_UP_SCOPE_SESSIONS_REVOKE,
  AdminApiError,
  canEditUsersRole,
  DEFAULT_ADMIN_LIST_PAGE_SIZE,
  getAdminSessions,
  isAuthExpiredError,
  mapSessionActionError,
  revokeAdminSession,
  type AdminSessionRecord,
  type AdminSessionsFilters,
  type OffsetPaginationFilters,
} from '../../features/auth/auth-client.js';
import { useAuth } from '../../features/auth/auth-context.js';
import { isAdminStepUpCancelledError, useAdminStepUp } from '../../features/auth/useAdminStepUp.js';

const EMPTY_FILTERS: AdminSessionsFilters = {
  query: '',
  authState: '',
  userId: '',
  deviceId: '',
  limit: DEFAULT_ADMIN_LIST_PAGE_SIZE,
  offset: 0,
};

function formatValue(value: string | null | undefined): string {
  if (!value) return 'n/a';
  return value;
}

function getSessionStateColor(authState: string): string {
  if (authState === 'authenticated_active') return 'green';
  if (authState.startsWith('revoked:')) return 'red';
  return 'orange';
}

export function SessionsPage(): JSX.Element {
  const navigate = useNavigate();
  const { accessToken, session, handleExpiredSession } = useAuth();
  const [draftFilters, setDraftFilters] = useState<AdminSessionsFilters>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<AdminSessionsFilters>(EMPTY_FILTERS);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const canWrite = canEditUsersRole(session);
  const { requestStepUp, stepUpModal } = useAdminStepUp({
    accessToken,
    onExpiredSession: () => {
      handleExpiredSession();
      navigate('/login', { replace: true, state: { from: '/sessions' } });
    },
  });
  const sessionsQuery = useQuery({
    queryKey: ['adminSessions', appliedFilters],
    queryFn: () => getAdminSessions(accessToken ?? '', appliedFilters),
    enabled: Boolean(accessToken),
  });

  const selectedSession = useMemo<AdminSessionRecord | null>(
    () => sessionsQuery.data?.items.find((item) => item.session_id === selectedSessionId) ?? null,
    [selectedSessionId, sessionsQuery.data?.items]
  );

  async function refreshSessionsState(preferredSessionId: string): Promise<void> {
    const listResult = await sessionsQuery.refetch();
    const items = listResult.data?.items ?? [];
    const nextSelectedSessionId = items.some((item) => item.session_id === preferredSessionId)
      ? preferredSessionId
      : (items[0]?.session_id ?? null);

    setSelectedSessionId(nextSelectedSessionId);
  }

  function applyPagination(nextPagination: OffsetPaginationFilters): void {
    setActionFeedback(null);
    setActionError(null);
    setDraftFilters((current) => ({
      ...current,
      ...nextPagination,
    }));
    setAppliedFilters((current) => ({
      ...current,
      ...nextPagination,
    }));
  }

  const revokeMutation = useMutation({
    mutationFn: async ({ sessionId, stepUpToken }: { sessionId: string; stepUpToken: string }) => {
      if (!accessToken) {
        throw new Error('Missing admin session');
      }

      return revokeAdminSession(accessToken, sessionId, stepUpToken);
    },
    onMutate: () => {
      setActionFeedback(null);
      setActionError(null);
    },
    onSuccess: async (_response, variables) => {
      try {
        await refreshSessionsState(variables.sessionId);
        setActionFeedback('Session revoked. The sessions list and selected detail were refreshed from the backend.');
      } catch (error) {
        if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
          handleExpiredSession();
          navigate('/login', { replace: true, state: { from: '/sessions' } });
          return;
        }

        setActionError('The session was revoked, but the follow-up refresh failed. Retry the list query.');
      }
    },
    onError: (error) => {
      if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
        handleExpiredSession();
        navigate('/login', { replace: true, state: { from: '/sessions' } });
        return;
      }

      setActionError(error instanceof AdminApiError ? mapSessionActionError(error.errorCode) : mapSessionActionError());
    },
  });

  useEffect(() => {
    if (sessionsQuery.error instanceof AdminApiError && isAuthExpiredError(sessionsQuery.error.errorCode)) {
      handleExpiredSession();
      navigate('/login', { replace: true, state: { from: '/sessions' } });
    }
  }, [handleExpiredSession, navigate, sessionsQuery.error]);

  useEffect(() => {
    const items = sessionsQuery.data?.items ?? [];
    if (items.length === 0) {
      setSelectedSessionId(null);
      return;
    }

    if (!selectedSessionId || !items.some((item) => item.session_id === selectedSessionId)) {
      setSelectedSessionId(items[0].session_id);
    }
  }, [selectedSessionId, sessionsQuery.data?.items]);

  async function runSessionRevoke(sessionId: string): Promise<void> {
    try {
      const stepUpToken = await requestStepUp({
        scope: ADMIN_STEP_UP_SCOPE_SESSIONS_REVOKE,
        actionLabel: 'Revoke session',
        description:
          'Confirm your password before revoking this session. The admin API will issue a short-lived step-up token for the destructive request.',
      });
      await revokeMutation.mutateAsync({ sessionId, stepUpToken });
    } catch (error) {
      if (isAdminStepUpCancelledError(error)) {
        return;
      }
    }
  }

  if (!accessToken) {
    return <ErrorState title="Admin session missing" description={formatAdminMissingSession('sessions')} />;
  }

  if (sessionsQuery.isLoading && !sessionsQuery.data) {
    return <LoadingState title="Loading sessions" />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={2} style={{ marginBottom: 8 }}>
          Sessions
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Inspect live auth continuity, filter by user or device, and revoke sessions with the same protected confirmation flow used across admin actions.
        </Typography.Paragraph>
      </div>

      <Alert
        type={canWrite ? 'success' : 'warning'}
        showIcon
        message={canWrite ? 'Write access available' : 'Read-only access'}
        description={
          canWrite
            ? 'Session revoke now asks for password confirmation first, then refreshes the filtered list after each successful action.'
            : 'This role can inspect sessions, but revoke controls remain disabled.'
        }
      />

      <Card>
        <Form
          layout="vertical"
          onFinish={() => {
            setActionFeedback(null);
            setActionError(null);
            setDraftFilters((current) => ({
              ...current,
              offset: 0,
            }));
            setAppliedFilters({
              ...draftFilters,
              offset: 0,
            });
          }}
        >
          <Flex gap={16} wrap="wrap" align="end">
            <Form.Item label="Search" style={{ minWidth: 240, flex: 1, marginBottom: 0 }}>
              <Input
                value={draftFilters.query}
                placeholder="sess_1 / u_1 / device_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    query: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Auth state" style={{ minWidth: 220, marginBottom: 0 }}>
              <Select
                value={draftFilters.authState}
                onChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    authState: value,
                  }))
                }
                options={[
                  { value: '', label: 'All states' },
                  { value: 'authenticated_active', label: 'authenticated_active' },
                  { value: 'authorization_disabled', label: 'authorization_disabled' },
                  { value: 'device_unbound', label: 'device_unbound' },
                  { value: 'device_disabled', label: 'device_disabled' },
                ]}
              />
            </Form.Item>
            <Form.Item label="User" style={{ minWidth: 180, marginBottom: 0 }}>
              <Input
                value={draftFilters.userId}
                placeholder="u_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    userId: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Device" style={{ minWidth: 180, marginBottom: 0 }}>
              <Input
                value={draftFilters.deviceId}
                placeholder="device_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    deviceId: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={sessionsQuery.isFetching}>
                Apply filters
              </Button>
              <Button
                onClick={() => {
                  setActionFeedback(null);
                  setActionError(null);
                  setDraftFilters(EMPTY_FILTERS);
                  setAppliedFilters(EMPTY_FILTERS);
                }}
              >
                Clear
              </Button>
            </Space>
          </Flex>
        </Form>
      </Card>

      <Flex gap={16} align="stretch" wrap="wrap">
        <Card title={`Sessions (${sessionsQuery.data?.total ?? 0})`} style={{ flex: '1 1 380px', minWidth: 320 }}>
          <OffsetPaginationControls
            filters={appliedFilters}
            response={sessionsQuery.data}
            loading={sessionsQuery.isFetching}
            onChange={applyPagination}
          />
          {sessionsQuery.isError ? (
            <ErrorState
              title="Sessions unavailable"
              description={formatAdminListError('session')}
              retryLabel="Retry sessions"
              onRetry={() => void sessionsQuery.refetch()}
            />
          ) : sessionsQuery.data && sessionsQuery.data.items.length > 0 ? (
            <List
              dataSource={sessionsQuery.data.items}
              renderItem={(item) => (
                <List.Item
                  key={item.session_id}
                  style={{
                    cursor: 'pointer',
                    paddingInline: 12,
                    borderRadius: 8,
                    background: item.session_id === selectedSessionId ? '#f0f5ff' : undefined,
                    border: item.session_id === selectedSessionId ? '1px solid #adc6ff' : '1px solid transparent',
                    marginBottom: 8,
                  }}
                  onClick={() => {
                    setActionFeedback(null);
                    setActionError(null);
                    setSelectedSessionId(item.session_id);
                  }}
                >
                  <List.Item.Meta
                    title={
                      <Space wrap>
                        <span>{item.session_id}</span>
                        <Tag color={getSessionStateColor(item.auth_state)}>{item.auth_state}</Tag>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <Typography.Text type="secondary">User: {item.user_id ?? 'n/a'}</Typography.Text>
                        <Typography.Text type="secondary">Device: {item.device_id ?? 'n/a'}</Typography.Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <EmptyState description={formatFilteredEmptyState('sessions')} />
          )}
        </Card>

        <Card title="Selected session" style={{ flex: '2 1 520px', minWidth: 360 }}>
          {actionFeedback ? <Alert type="success" showIcon message={actionFeedback} style={{ marginBottom: 16 }} /> : null}
          {actionError ? <Alert type="error" showIcon message={actionError} style={{ marginBottom: 16 }} /> : null}

          {selectedSession ? (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Descriptions bordered column={2} size="small">
                <Descriptions.Item label="Session ID">{selectedSession.session_id}</Descriptions.Item>
                <Descriptions.Item label="Auth state">{selectedSession.auth_state}</Descriptions.Item>
                <Descriptions.Item label="User">{formatValue(selectedSession.user_id)}</Descriptions.Item>
                <Descriptions.Item label="Device">{formatValue(selectedSession.device_id)}</Descriptions.Item>
                <Descriptions.Item label="Issued at">{selectedSession.issued_at}</Descriptions.Item>
                <Descriptions.Item label="Expires at">{selectedSession.expires_at}</Descriptions.Item>
                <Descriptions.Item label="Last seen" span={2}>
                  {selectedSession.last_seen_at}
                </Descriptions.Item>
              </Descriptions>

              <Flex gap={12} wrap="wrap">
                <Button
                  danger
                  disabled={!canWrite || revokeMutation.isPending}
                  loading={revokeMutation.isPending}
                  onClick={() => {
                    void runSessionRevoke(selectedSession.session_id);
                  }}
                >
                  Revoke session
                </Button>
                <Tag color={getSessionStateColor(selectedSession.auth_state)}>
                  Current state: {selectedSession.auth_state}
                </Tag>
              </Flex>

              <Alert
                type={canWrite ? 'warning' : 'info'}
                showIcon
                message="Danger zone"
                description={
                  canWrite
                    ? 'Session revocation is audited server-side. Each action requires password confirmation, a short-lived step-up token, and a backend refresh after success.'
                    : 'This role can review sessions, but revoke actions remain disabled.'
                }
              />
            </Space>
          ) : sessionsQuery.isFetching ? (
            <LoadingState title="Refreshing selected session" />
          ) : selectedSessionId ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={formatSelectionEmptyState('a session', 'auth state and revoke controls')}
            />
          ) : (
            <EmptyState description={formatSelectionEmptyState('a session', 'auth state and revoke controls')} />
          )}
        </Card>
      </Flex>
      {stepUpModal}
    </Space>
  );
}
