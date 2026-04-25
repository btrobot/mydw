import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Button, Card, Descriptions, Empty, Flex, Form, Input, List, Select, Space, Tag, Typography } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '../../components/states/EmptyState.js';
import { ErrorState } from '../../components/states/ErrorState.js';
import { LoadingState } from '../../components/states/LoadingState.js';
import {
  AdminApiError,
  canEditUsersRole,
  formatPageSummary,
  getAdminUserDetail,
  getAdminUsers,
  isAuthExpiredError,
  mapAdminActionError,
  restoreAdminUser,
  revokeAdminUser,
  type AdminUserRecord,
  type AdminUsersFilters,
} from '../../features/auth/auth-client.js';
import { useAuth } from '../../features/auth/auth-context.js';

const EMPTY_FILTERS: AdminUsersFilters = {
  query: '',
  status: '',
  licenseStatus: '',
};

function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return 'n/a';
  return String(value);
}

function renderEntitlements(user: AdminUserRecord): JSX.Element {
  if (user.entitlements.length === 0) {
    return <Tag>none</Tag>;
  }

  return (
    <>
      {user.entitlements.map((entitlement) => (
        <Tag key={entitlement}>{entitlement}</Tag>
      ))}
    </>
  );
}

export function UsersPage(): JSX.Element {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { accessToken, session, handleExpiredSession } = useAuth();
  const [draftFilters, setDraftFilters] = useState<AdminUsersFilters>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<AdminUsersFilters>(EMPTY_FILTERS);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const canWrite = canEditUsersRole(session);
  const usersQuery = useQuery({
    queryKey: ['adminUsers', appliedFilters],
    queryFn: () => getAdminUsers(accessToken ?? '', appliedFilters),
    enabled: Boolean(accessToken),
  });

  const selectedUser = useMemo(
    () => usersQuery.data?.items.find((item) => item.id === selectedUserId) ?? null,
    [selectedUserId, usersQuery.data?.items]
  );

  const detailQuery = useQuery({
    queryKey: ['adminUserDetail', selectedUserId],
    queryFn: () => getAdminUserDetail(accessToken ?? '', selectedUserId ?? ''),
    enabled: Boolean(accessToken && selectedUserId),
  });

  async function refreshUsersState(preferredUserId: string): Promise<void> {
    if (!accessToken) return;

    const listResult = await usersQuery.refetch();
    const items = listResult.data?.items ?? [];
    const nextSelectedUserId = items.some((item) => item.id === preferredUserId)
      ? preferredUserId
      : (items[0]?.id ?? null);

    if (nextSelectedUserId) {
      await queryClient.fetchQuery({
        queryKey: ['adminUserDetail', nextSelectedUserId],
        queryFn: () => getAdminUserDetail(accessToken, nextSelectedUserId),
      });
    }

    setSelectedUserId(nextSelectedUserId);
  }

  const userActionMutation = useMutation({
    mutationFn: async ({ action, userId }: { action: 'revoke' | 'restore'; userId: string }) => {
      if (!accessToken) {
        throw new Error('Missing admin session');
      }

      return action === 'revoke' ? revokeAdminUser(accessToken, userId) : restoreAdminUser(accessToken, userId);
    },
    onMutate: () => {
      setActionFeedback(null);
      setActionError(null);
    },
    onSuccess: async (_response, variables) => {
      try {
        await refreshUsersState(variables.userId);
        setActionFeedback(
          variables.action === 'revoke'
            ? 'User access revoked. The list and detail panel were refreshed from the backend.'
            : 'User access restored. The list and detail panel were refreshed from the backend.'
        );
      } catch (error) {
        if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
          handleExpiredSession();
          navigate('/login', { replace: true, state: { from: '/users' } });
          return;
        }

        setActionError(
          variables.action === 'revoke'
            ? 'User access was revoked, but the follow-up refresh failed. Retry the list or detail query.'
            : 'User access was restored, but the follow-up refresh failed. Retry the list or detail query.'
        );
      }
    },
    onError: (error) => {
      if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
        handleExpiredSession();
        navigate('/login', { replace: true, state: { from: '/users' } });
        return;
      }

      setActionError(error instanceof AdminApiError ? mapAdminActionError(error.errorCode) : mapAdminActionError());
    },
  });

  useEffect(() => {
    const error = usersQuery.error ?? detailQuery.error;
    if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
      handleExpiredSession();
      navigate('/login', { replace: true, state: { from: '/users' } });
    }
  }, [detailQuery.error, handleExpiredSession, navigate, usersQuery.error]);

  useEffect(() => {
    const items = usersQuery.data?.items ?? [];
    if (items.length === 0) {
      setSelectedUserId(null);
      return;
    }

    if (!selectedUserId || !items.some((item) => item.id === selectedUserId)) {
      setSelectedUserId(items[0].id);
    }
  }, [selectedUserId, usersQuery.data?.items]);

  const isRevoking = userActionMutation.isPending && userActionMutation.variables?.action === 'revoke';
  const isRestoring = userActionMutation.isPending && userActionMutation.variables?.action === 'restore';
  const selectedDetail = detailQuery.data;
  const selectedUserIsRevoked =
    selectedDetail?.status === 'revoked' || selectedDetail?.license_status === 'revoked';

  if (!accessToken) {
    return <ErrorState title="Admin session missing" description="Please sign in again before loading managed users." />;
  }

  if (usersQuery.isLoading && !usersQuery.data) {
    return <LoadingState title="Loading managed users" />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={2} style={{ marginBottom: 8 }}>
          Users
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Day 3 starts the users page migration with live filters, route-guard-safe detail loading, and a read-only-aware detail rail.
        </Typography.Paragraph>
      </div>

      <Alert
        type={canWrite ? 'success' : 'warning'}
        showIcon
        message={canWrite ? 'Write-capable role detected' : 'Read-only role detected'}
        description={
          canWrite
            ? 'Day 3.1 enables revoke / restore and automatically refreshes list/detail state after each successful action.'
            : 'This role can inspect users, but revoke / restore / edit controls stay disabled during and after migration.'
        }
      />

      <Card>
        <Form
          layout="vertical"
          onFinish={() => {
            setActionFeedback(null);
            setActionError(null);
            setAppliedFilters({ ...draftFilters });
          }}
        >
          <Flex gap={16} wrap="wrap" align="end">
            <Form.Item label="Search" style={{ minWidth: 240, flex: 1, marginBottom: 0 }}>
              <Input
                value={draftFilters.query}
                placeholder="alice / alice@example.com / u_1"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    query: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Status" style={{ minWidth: 180, marginBottom: 0 }}>
              <Select
                value={draftFilters.status}
                onChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    status: value,
                  }))
                }
                options={[
                  { value: '', label: 'All statuses' },
                  { value: 'active', label: 'active' },
                  { value: 'revoked', label: 'revoked' },
                ]}
              />
            </Form.Item>
            <Form.Item label="License" style={{ minWidth: 180, marginBottom: 0 }}>
              <Select
                value={draftFilters.licenseStatus}
                onChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    licenseStatus: value,
                  }))
                }
                options={[
                  { value: '', label: 'All licenses' },
                  { value: 'active', label: 'active' },
                  { value: 'expired', label: 'expired' },
                  { value: 'revoked', label: 'revoked' },
                ]}
              />
            </Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={usersQuery.isFetching}>
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
        <Card title={`Users (${usersQuery.data?.total ?? 0})`} style={{ flex: '1 1 360px', minWidth: 320 }}>
          {usersQuery.data ? (
            <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
              {formatPageSummary(usersQuery.data)}
            </Typography.Text>
          ) : null}
          {usersQuery.isError ? (
            <ErrorState
              title="User list unavailable"
              description="The React users list could not be loaded from the admin API."
              retryLabel="Retry users"
              onRetry={() => void usersQuery.refetch()}
            />
          ) : usersQuery.data && usersQuery.data.items.length > 0 ? (
            <List
              dataSource={usersQuery.data.items}
              renderItem={(item) => (
                <List.Item
                  key={item.id}
                  style={{
                    cursor: 'pointer',
                    paddingInline: 12,
                    borderRadius: 8,
                    background: item.id === selectedUserId ? '#f0f5ff' : undefined,
                    border: item.id === selectedUserId ? '1px solid #adc6ff' : '1px solid transparent',
                    marginBottom: 8,
                  }}
                  onClick={() => {
                    setActionFeedback(null);
                    setActionError(null);
                    setSelectedUserId(item.id);
                  }}
                >
                  <List.Item.Meta
                    title={
                      <Space wrap>
                        <span>{item.display_name ?? item.username}</span>
                        <Tag>{item.status ?? 'unknown'}</Tag>
                        <Tag color={item.license_status === 'active' ? 'green' : 'default'}>
                          {item.license_status ?? 'no-license'}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <Typography.Text type="secondary">{item.username}</Typography.Text>
                        <Typography.Text type="secondary">{item.email ?? 'No email on record'}</Typography.Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <EmptyState description="No managed users matched the current filters." />
          )}
        </Card>

        <Card title="Selected user" style={{ flex: '2 1 480px', minWidth: 360 }}>
          {detailQuery.isLoading ? (
            <LoadingState title="Loading selected user" />
          ) : detailQuery.isError ? (
            <ErrorState
              title="User detail unavailable"
              description="The selected user detail request failed."
              retryLabel="Retry detail"
              onRetry={() => void detailQuery.refetch()}
            />
          ) : detailQuery.data ? (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {actionFeedback ? <Alert type="success" showIcon message={actionFeedback} /> : null}
              {actionError ? <Alert type="error" showIcon message={actionError} /> : null}

              <Descriptions bordered column={2} size="small">
                <Descriptions.Item label="User ID">{detailQuery.data.id}</Descriptions.Item>
                <Descriptions.Item label="Username">{detailQuery.data.username}</Descriptions.Item>
                <Descriptions.Item label="Display name">{formatValue(detailQuery.data.display_name)}</Descriptions.Item>
                <Descriptions.Item label="Email">{formatValue(detailQuery.data.email)}</Descriptions.Item>
                <Descriptions.Item label="Tenant">{formatValue(detailQuery.data.tenant_id)}</Descriptions.Item>
                <Descriptions.Item label="Status">{formatValue(detailQuery.data.status)}</Descriptions.Item>
                <Descriptions.Item label="License">{formatValue(detailQuery.data.license_status)}</Descriptions.Item>
                <Descriptions.Item label="License expiry">{formatValue(detailQuery.data.license_expires_at)}</Descriptions.Item>
                <Descriptions.Item label="Device count">{formatValue(detailQuery.data.device_count)}</Descriptions.Item>
                <Descriptions.Item label="Last seen">{formatValue(detailQuery.data.last_seen_at)}</Descriptions.Item>
                <Descriptions.Item label="Entitlements" span={2}>
                  {renderEntitlements(detailQuery.data)}
                </Descriptions.Item>
              </Descriptions>

              <Flex gap={12} wrap="wrap">
                <Button
                  danger
                  disabled={!canWrite || isRevoking || isRestoring}
                  loading={isRevoking}
                  onClick={() => {
                    if (!selectedDetail) return;
                    void userActionMutation.mutateAsync({ action: 'revoke', userId: selectedDetail.id });
                  }}
                >
                  Revoke user
                </Button>
                <Button
                  disabled={!canWrite || isRevoking || isRestoring}
                  loading={isRestoring}
                  onClick={() => {
                    if (!selectedDetail) return;
                    void userActionMutation.mutateAsync({ action: 'restore', userId: selectedDetail.id });
                  }}
                >
                  Restore user
                </Button>
                {selectedUserIsRevoked ? (
                  <Tag color="red">Current state: revoked</Tag>
                ) : (
                  <Tag color="green">Current state: active-or-readable</Tag>
                )}
              </Flex>

              <Alert
                type={canWrite ? 'warning' : 'info'}
                showIcon
                message="Danger zone"
                description={
                  canWrite
                    ? 'Revoke / restore are audited server-side and this page immediately refetches list and detail data after success.'
                    : 'This admin role can view user detail only. Revoke / restore controls remain disabled.'
                }
              />
            </Space>
          ) : usersQuery.isFetching ? (
            <LoadingState title="Refreshing user detail" />
          ) : selectedUser ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select a user to inspect detail." />
          ) : (
            <EmptyState description="Choose a user from the list to inspect authorization detail." />
          )}
        </Card>
      </Flex>
    </Space>
  );
}
