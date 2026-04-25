import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Button, Card, Descriptions, Empty, Flex, Form, Input, List, Select, Space, Tag, Typography } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { OffsetPaginationControls } from '../../components/pagination/OffsetPaginationControls.js';
import { EmptyState } from '../../components/states/EmptyState.js';
import { ErrorState } from '../../components/states/ErrorState.js';
import { LoadingState } from '../../components/states/LoadingState.js';
import {
  ADMIN_STEP_UP_SCOPE_DEVICES_WRITE,
  AdminApiError,
  canEditUsersRole,
  DEFAULT_ADMIN_LIST_PAGE_SIZE,
  disableAdminDevice,
  getAdminDeviceDetail,
  getAdminDevices,
  isAuthExpiredError,
  mapDeviceActionError,
  rebindAdminDevice,
  unbindAdminDevice,
  type AdminDeviceRecord,
  type AdminDevicesFilters,
  type OffsetPaginationFilters,
} from '../../features/auth/auth-client.js';
import { useAuth } from '../../features/auth/auth-context.js';
import { isAdminStepUpCancelledError, useAdminStepUp } from '../../features/auth/useAdminStepUp.js';

const EMPTY_FILTERS: AdminDevicesFilters = {
  query: '',
  status: '',
  userId: '',
  limit: DEFAULT_ADMIN_LIST_PAGE_SIZE,
  offset: 0,
};

type DeviceAction = 'unbind' | 'disable' | 'rebind';
type DeviceActionVariables =
  | { action: 'unbind'; deviceId: string }
  | { action: 'disable'; deviceId: string }
  | { action: 'rebind'; deviceId: string; userId: string; clientVersion: string };

function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return 'n/a';
  return String(value);
}

function getDeviceStatusColor(status: string | null | undefined): string {
  if (status === 'bound') return 'green';
  if (status === 'disabled') return 'red';
  if (status === 'unbound') return 'orange';
  return 'default';
}

export function DevicesPage(): JSX.Element {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { accessToken, session, handleExpiredSession } = useAuth();
  const [draftFilters, setDraftFilters] = useState<AdminDevicesFilters>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<AdminDevicesFilters>(EMPTY_FILTERS);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [rebindUserId, setRebindUserId] = useState('');
  const [rebindClientVersion, setRebindClientVersion] = useState('0.2.0');
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const canWrite = canEditUsersRole(session);
  const { requestStepUp, stepUpModal } = useAdminStepUp({
    accessToken,
    onExpiredSession: () => {
      handleExpiredSession();
      navigate('/login', { replace: true, state: { from: '/devices' } });
    },
  });
  const devicesQuery = useQuery({
    queryKey: ['adminDevices', appliedFilters],
    queryFn: () => getAdminDevices(accessToken ?? '', appliedFilters),
    enabled: Boolean(accessToken),
  });

  const selectedDevice = useMemo(
    () => devicesQuery.data?.items.find((item) => item.device_id === selectedDeviceId) ?? null,
    [devicesQuery.data?.items, selectedDeviceId]
  );

  const detailQuery = useQuery({
    queryKey: ['adminDeviceDetail', selectedDeviceId],
    queryFn: () => getAdminDeviceDetail(accessToken ?? '', selectedDeviceId ?? ''),
    enabled: Boolean(accessToken && selectedDeviceId),
  });

  async function refreshDevicesState(preferredDeviceId: string): Promise<void> {
    if (!accessToken) return;

    const listResult = await devicesQuery.refetch();
    const items = listResult.data?.items ?? [];
    const nextSelectedDeviceId = items.some((item) => item.device_id === preferredDeviceId)
      ? preferredDeviceId
      : (items[0]?.device_id ?? null);

    if (nextSelectedDeviceId) {
      await queryClient.fetchQuery({
        queryKey: ['adminDeviceDetail', nextSelectedDeviceId],
        queryFn: () => getAdminDeviceDetail(accessToken, nextSelectedDeviceId),
      });
    }

    setSelectedDeviceId(nextSelectedDeviceId);
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

  const deviceActionMutation = useMutation({
    mutationFn: async (
      variables:
        | { action: 'unbind'; deviceId: string; stepUpToken: string }
        | { action: 'disable'; deviceId: string; stepUpToken: string }
        | { action: 'rebind'; deviceId: string; userId: string; clientVersion: string; stepUpToken: string }
    ) => {
      if (!accessToken) {
        throw new Error('Missing admin session');
      }

      if (variables.action === 'unbind') {
        return unbindAdminDevice(accessToken, variables.deviceId, variables.stepUpToken);
      }

      if (variables.action === 'disable') {
        return disableAdminDevice(accessToken, variables.deviceId, variables.stepUpToken);
      }

      return rebindAdminDevice(accessToken, variables.deviceId, {
        user_id: variables.userId,
        client_version: variables.clientVersion,
      }, variables.stepUpToken);
    },
    onMutate: () => {
      setActionFeedback(null);
      setActionError(null);
    },
    onSuccess: async (_response, variables) => {
      try {
        await refreshDevicesState(variables.deviceId);
        if (variables.action === 'unbind') {
          setActionFeedback('Device unbound. The list and detail panel were refreshed from the backend.');
          return;
        }
        if (variables.action === 'disable') {
          setActionFeedback('Device disabled. The list and detail panel were refreshed from the backend.');
          return;
        }
        setActionFeedback('Device rebound. The list and detail panel were refreshed from the backend.');
      } catch (error) {
        if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
          handleExpiredSession();
          navigate('/login', { replace: true, state: { from: '/devices' } });
          return;
        }

        setActionError('The device action completed, but the follow-up refresh failed. Retry the list or detail query.');
      }
    },
    onError: (error) => {
      if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
        handleExpiredSession();
        navigate('/login', { replace: true, state: { from: '/devices' } });
        return;
      }

      setActionError(error instanceof AdminApiError ? mapDeviceActionError(error.errorCode) : mapDeviceActionError());
    },
  });

  useEffect(() => {
    const error = devicesQuery.error ?? detailQuery.error;
    if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
      handleExpiredSession();
      navigate('/login', { replace: true, state: { from: '/devices' } });
    }
  }, [detailQuery.error, devicesQuery.error, handleExpiredSession, navigate]);

  useEffect(() => {
    const items = devicesQuery.data?.items ?? [];
    if (items.length === 0) {
      setSelectedDeviceId(null);
      return;
    }

    if (!selectedDeviceId || !items.some((item) => item.device_id === selectedDeviceId)) {
      setSelectedDeviceId(items[0].device_id);
    }
  }, [devicesQuery.data?.items, selectedDeviceId]);

  useEffect(() => {
    const detail = detailQuery.data;
    setRebindUserId(detail?.user_id ?? '');
    setRebindClientVersion(detail?.client_version ?? '0.2.0');
  }, [detailQuery.data]);

  const isMutating = deviceActionMutation.isPending;
  const actionType = deviceActionMutation.variables?.action;
  const selectedDetail = detailQuery.data;

  async function runDeviceAction(variables: DeviceActionVariables): Promise<void> {
    const descriptions: Record<DeviceAction, string> = {
      unbind: 'Confirm your password before unbinding this device. The admin API will issue a short-lived step-up token for the destructive request.',
      disable: 'Confirm your password before disabling this device. The admin API will issue a short-lived step-up token for the destructive request.',
      rebind: 'Confirm your password before rebinding this device. The admin API will issue a short-lived step-up token for the destructive request.',
    };
    const labels: Record<DeviceAction, string> = {
      unbind: 'Unbind device',
      disable: 'Disable device',
      rebind: 'Rebind device',
    };

    try {
      const stepUpToken = await requestStepUp({
        scope: ADMIN_STEP_UP_SCOPE_DEVICES_WRITE,
        actionLabel: labels[variables.action],
        description: descriptions[variables.action],
      });
      await deviceActionMutation.mutateAsync({ ...variables, stepUpToken });
    } catch (error) {
      if (isAdminStepUpCancelledError(error)) {
        return;
      }
    }
  }

  if (!accessToken) {
    return <ErrorState title="Admin session missing" description="Please sign in again before loading managed devices." />;
  }

  if (devicesQuery.isLoading && !devicesQuery.data) {
    return <LoadingState title="Loading managed devices" />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={2} style={{ marginBottom: 8 }}>
          Devices
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Day 3.2 migrates the devices list/detail route into React and reuses the users-style mutation refresh sequence.
        </Typography.Paragraph>
      </div>

      <Alert
        type={canWrite ? 'success' : 'warning'}
        showIcon
        message={canWrite ? 'Write-capable role detected' : 'Read-only role detected'}
        description={
          canWrite
            ? 'Unbind / disable / rebind now ask for password confirmation first, then refresh list/detail state after each successful device action.'
            : 'This role can inspect devices, but all device mutations remain disabled.'
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
                placeholder="device_1 / u_1 / 0.2.0"
                onChange={(event) =>
                  setDraftFilters((current) => ({
                    ...current,
                    query: event.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Device status" style={{ minWidth: 180, marginBottom: 0 }}>
              <Select
                value={draftFilters.status}
                onChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    status: value,
                  }))
                }
                options={[
                  { value: '', label: 'All device states' },
                  { value: 'bound', label: 'bound' },
                  { value: 'unbound', label: 'unbound' },
                  { value: 'disabled', label: 'disabled' },
                ]}
              />
            </Form.Item>
            <Form.Item label="Bound user" style={{ minWidth: 180, marginBottom: 0 }}>
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
            <Space>
              <Button type="primary" htmlType="submit" loading={devicesQuery.isFetching}>
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
        <Card title={`Devices (${devicesQuery.data?.total ?? 0})`} style={{ flex: '1 1 360px', minWidth: 320 }}>
          <OffsetPaginationControls
            filters={appliedFilters}
            response={devicesQuery.data}
            loading={devicesQuery.isFetching}
            onChange={applyPagination}
          />
          {devicesQuery.isError ? (
            <ErrorState
              title="Device list unavailable"
              description="The React devices list could not be loaded from the admin API."
              retryLabel="Retry devices"
              onRetry={() => void devicesQuery.refetch()}
            />
          ) : devicesQuery.data && devicesQuery.data.items.length > 0 ? (
            <List
              dataSource={devicesQuery.data.items}
              renderItem={(item) => (
                <List.Item
                  key={item.device_id}
                  style={{
                    cursor: 'pointer',
                    paddingInline: 12,
                    borderRadius: 8,
                    background: item.device_id === selectedDeviceId ? '#f0f5ff' : undefined,
                    border: item.device_id === selectedDeviceId ? '1px solid #adc6ff' : '1px solid transparent',
                    marginBottom: 8,
                  }}
                  onClick={() => {
                    setActionFeedback(null);
                    setActionError(null);
                    setSelectedDeviceId(item.device_id);
                  }}
                >
                  <List.Item.Meta
                    title={
                      <Space wrap>
                        <span>{item.device_id}</span>
                        <Tag color={getDeviceStatusColor(item.device_status)}>{item.device_status}</Tag>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <Typography.Text type="secondary">{item.user_id ?? 'unbound'}</Typography.Text>
                        <Typography.Text type="secondary">
                          Client: {item.client_version ?? 'n/a'}
                        </Typography.Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <EmptyState description="No devices matched the current filters." />
          )}
        </Card>

        <Card title="Selected device" style={{ flex: '2 1 520px', minWidth: 360 }}>
          {detailQuery.isLoading ? (
            <LoadingState title="Loading selected device" />
          ) : detailQuery.isError ? (
            <ErrorState
              title="Device detail unavailable"
              description="The selected device detail request failed."
              retryLabel="Retry detail"
              onRetry={() => void detailQuery.refetch()}
            />
          ) : detailQuery.data ? (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {actionFeedback ? <Alert type="success" showIcon message={actionFeedback} /> : null}
              {actionError ? <Alert type="error" showIcon message={actionError} /> : null}

              <Descriptions bordered column={2} size="small">
                <Descriptions.Item label="Device ID">{detailQuery.data.device_id}</Descriptions.Item>
                <Descriptions.Item label="Bound user">{formatValue(detailQuery.data.user_id ?? 'unbound')}</Descriptions.Item>
                <Descriptions.Item label="Device status">{formatValue(detailQuery.data.device_status)}</Descriptions.Item>
                <Descriptions.Item label="Client version">{formatValue(detailQuery.data.client_version)}</Descriptions.Item>
                <Descriptions.Item label="First bound">{formatValue(detailQuery.data.first_bound_at)}</Descriptions.Item>
                <Descriptions.Item label="Last seen">{formatValue(detailQuery.data.last_seen_at)}</Descriptions.Item>
              </Descriptions>

              <Card size="small" title="Rebind device">
                <Form
                  layout="vertical"
                  onFinish={() => {
                    if (!selectedDetail) return;

                    setActionFeedback(null);
                    setActionError(null);
                    void runDeviceAction({
                      action: 'rebind',
                      deviceId: selectedDetail.device_id,
                      userId: rebindUserId.trim(),
                      clientVersion: rebindClientVersion.trim(),
                    });
                  }}
                >
                  <Flex gap={16} wrap="wrap" align="end">
                    <Form.Item label="Target user id" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
                      <Input
                        value={rebindUserId}
                        placeholder="u_1"
                        disabled={!canWrite || isMutating}
                        onChange={(event) => setRebindUserId(event.target.value)}
                      />
                    </Form.Item>
                    <Form.Item label="Client version" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
                      <Input
                        value={rebindClientVersion}
                        placeholder="0.2.0"
                        disabled={!canWrite || isMutating}
                        onChange={(event) => setRebindClientVersion(event.target.value)}
                      />
                    </Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      disabled={!canWrite || isMutating || !rebindUserId.trim()}
                      loading={actionType === 'rebind' && isMutating}
                    >
                      Rebind device
                    </Button>
                  </Flex>
                </Form>
              </Card>

              <Flex gap={12} wrap="wrap">
                <Button
                  disabled={!canWrite || isMutating || !detailQuery.data.user_id}
                  loading={actionType === 'unbind' && isMutating}
                  onClick={() => {
                    void runDeviceAction({ action: 'unbind', deviceId: detailQuery.data.device_id });
                  }}
                >
                  Unbind device
                </Button>
                <Button
                  danger
                  disabled={!canWrite || isMutating || detailQuery.data.device_status === 'disabled'}
                  loading={actionType === 'disable' && isMutating}
                  onClick={() => {
                    void runDeviceAction({ action: 'disable', deviceId: detailQuery.data.device_id });
                  }}
                >
                  Disable device
                </Button>
                <Tag color={getDeviceStatusColor(detailQuery.data.device_status)}>
                  Current state: {detailQuery.data.device_status}
                </Tag>
              </Flex>

              <Alert
                type={canWrite ? 'warning' : 'info'}
                showIcon
                message="Danger zone"
                description={
                  canWrite
                    ? 'Unbind / disable / rebind are audited server-side. Before each destructive action, this page confirms your password, obtains a short-lived step-up token, then immediately refetches list and detail data after success.'
                    : 'This admin role can view device detail only. Device mutation controls remain disabled.'
                }
              />
            </Space>
          ) : devicesQuery.isFetching ? (
            <LoadingState title="Refreshing device detail" />
          ) : selectedDevice ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Select a device to inspect detail." />
          ) : (
            <EmptyState description="Choose a device from the list to inspect binding state." />
          )}
        </Card>
      </Flex>
      {stepUpModal}
    </Space>
  );
}
