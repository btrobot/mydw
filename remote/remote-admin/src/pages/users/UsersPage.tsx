import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, Button, Card, Descriptions, Empty, Flex, Form, Input, List, Modal, Select, Space, Tag, Typography } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { OffsetPaginationControls } from '../../components/pagination/OffsetPaginationControls.js';
import { EmptyState } from '../../components/states/EmptyState.js';
import { ErrorState } from '../../components/states/ErrorState.js';
import { LoadingState } from '../../components/states/LoadingState.js';
import {
  formatAdminDetailError,
  formatAdminListError,
  formatAdminMissingSession,
  formatFilteredEmptyState,
  formatSelectionEmptyState,
} from '../../components/states/adminCopy.js';
import {
  ADMIN_STEP_UP_SCOPE_USERS_WRITE,
  AdminApiError,
  type AdminUserCreateRequest,
  type AdminUserUpdateRequest,
  canEditUsersRole,
  createAdminUser,
  DEFAULT_ADMIN_LIST_PAGE_SIZE,
  getAdminUserDetail,
  getAdminUsers,
  isAuthExpiredError,
  mapAdminActionError,
  restoreAdminUser,
  revokeAdminUser,
  updateAdminUser,
  type AdminUserRecord,
  type AdminUsersFilters,
  type OffsetPaginationFilters,
} from '../../features/auth/auth-client.js';
import { useAuth } from '../../features/auth/auth-context.js';
import { isAdminStepUpCancelledError, useAdminStepUp } from '../../features/auth/useAdminStepUp.js';

const EMPTY_FILTERS: AdminUsersFilters = {
  query: '',
  status: '',
  licenseStatus: '',
  limit: DEFAULT_ADMIN_LIST_PAGE_SIZE,
  offset: 0,
};

type UserEditDraft = {
  displayName: string;
  licenseStatus: string;
  licenseExpiresAt: string;
  entitlements: string;
};

type CreateUserFormValues = {
  username: string;
  password: string;
  display_name: string;
  email: string;
  tenant_id: string;
  license_status: 'active' | 'revoked' | 'disabled';
  license_expires_at: string;
  entitlements: string;
};

const EMPTY_USER_EDIT_DRAFT: UserEditDraft = {
  displayName: '',
  licenseStatus: '',
  licenseExpiresAt: '',
  entitlements: '',
};

const EMPTY_CREATE_USER_FORM_VALUES: CreateUserFormValues = {
  username: '',
  password: '',
  display_name: '',
  email: '',
  tenant_id: '',
  license_status: 'active',
  license_expires_at: '',
  entitlements: '',
};

function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return 'n/a';
  return String(value);
}

function formatUserEditDraft(detail?: AdminUserRecord | null): UserEditDraft {
  if (!detail) {
    return EMPTY_USER_EDIT_DRAFT;
  }

  return {
    displayName: detail.display_name ?? '',
    licenseStatus: detail.license_status ?? '',
    licenseExpiresAt: detail.license_expires_at ?? '',
    entitlements: detail.entitlements.join(', '),
  };
}

function parseEntitlementsInput(value: string): string[] {
  const seen = new Set<string>();
  const parsed: string[] = [];
  for (const entry of value.split(/[\n,]/)) {
    const normalized = entry.trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    parsed.push(normalized);
  }
  return parsed;
}

function areStringArraysEqual(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((value, index) => value === right[index]);
}

function buildUserUpdatePayload(detail: AdminUserRecord, draft: UserEditDraft): AdminUserUpdateRequest {
  const payload: AdminUserUpdateRequest = {};

  if (draft.displayName !== (detail.display_name ?? '')) {
    payload.display_name = draft.displayName;
  }

  if (draft.licenseStatus !== (detail.license_status ?? '')) {
    payload.license_status = draft.licenseStatus;
  }

  const normalizedLicenseExpiry = draft.licenseExpiresAt.trim();
  if (normalizedLicenseExpiry && normalizedLicenseExpiry !== (detail.license_expires_at ?? '')) {
    payload.license_expires_at = normalizedLicenseExpiry;
  }

  const normalizedEntitlements = parseEntitlementsInput(draft.entitlements);
  if (!areStringArraysEqual(normalizedEntitlements, detail.entitlements)) {
    payload.entitlements = normalizedEntitlements;
  }

  return payload;
}

function buildUserCreatePayload(values: CreateUserFormValues): AdminUserCreateRequest {
  const normalizedLicenseExpiry = values.license_expires_at.trim();

  return {
    username: values.username.trim(),
    password: values.password,
    display_name: values.display_name.trim() || undefined,
    email: values.email.trim() || undefined,
    tenant_id: values.tenant_id.trim() || undefined,
    license_status: values.license_status,
    license_expires_at: normalizedLicenseExpiry || undefined,
    entitlements: parseEntitlementsInput(values.entitlements),
  };
}

function applyValidationErrorsToForm(
  form: ReturnType<typeof Form.useForm<CreateUserFormValues>>[0],
  error: unknown
): boolean {
  if (!(error instanceof AdminApiError) || !Array.isArray(error.details)) {
    return false;
  }

  const fieldErrors = error.details
    .map((issue) => {
      if (!issue || typeof issue !== 'object') {
        return null;
      }
      const loc = Array.isArray((issue as { loc?: unknown }).loc) ? (issue as { loc: unknown[] }).loc : null;
      const msg = typeof (issue as { msg?: unknown }).msg === 'string' ? (issue as { msg: string }).msg : 'Invalid value.';
      const fieldName = typeof loc?.[loc.length - 1] === 'string' ? (loc[loc.length - 1] as string) : null;
      if (!fieldName) {
        return null;
      }
      return {
        name: fieldName as keyof CreateUserFormValues,
        errors: [msg],
      };
    })
    .filter((value): value is { name: keyof CreateUserFormValues; errors: string[] } => value !== null);

  if (fieldErrors.length === 0) {
    return false;
  }

  form.setFields(fieldErrors);
  return true;
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
  const [createForm] = Form.useForm<CreateUserFormValues>();
  const [draftFilters, setDraftFilters] = useState<AdminUsersFilters>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<AdminUsersFilters>(EMPTY_FILTERS);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<UserEditDraft>(EMPTY_USER_EDIT_DRAFT);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createFormError, setCreateFormError] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const canWrite = canEditUsersRole(session);
  const { requestStepUp, stepUpModal } = useAdminStepUp({
    accessToken,
    onExpiredSession: () => {
      handleExpiredSession();
      navigate('/login', { replace: true, state: { from: '/users' } });
    },
  });
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

  async function refreshUsersState(
    preferredUserId: string,
    options?: {
      revealInDefaultList?: boolean;
    }
  ): Promise<void> {
    if (!accessToken) return;

    let nextFilters = appliedFilters;
    let listResult = await queryClient.fetchQuery({
      queryKey: ['adminUsers', appliedFilters],
      queryFn: () => getAdminUsers(accessToken, appliedFilters),
    });

    if (options?.revealInDefaultList && !listResult.items.some((item) => item.id === preferredUserId)) {
      nextFilters = EMPTY_FILTERS;
      setDraftFilters(EMPTY_FILTERS);
      setAppliedFilters(EMPTY_FILTERS);
      listResult = await queryClient.fetchQuery({
        queryKey: ['adminUsers', EMPTY_FILTERS],
        queryFn: () => getAdminUsers(accessToken, EMPTY_FILTERS),
      });
    }

    const items = listResult.items ?? [];
    const nextSelectedUserId = items.some((item) => item.id === preferredUserId)
      ? preferredUserId
      : (options?.revealInDefaultList ? preferredUserId : (items[0]?.id ?? null));

    if (nextSelectedUserId) {
      await queryClient.fetchQuery({
        queryKey: ['adminUserDetail', nextSelectedUserId],
        queryFn: () => getAdminUserDetail(accessToken, nextSelectedUserId),
      });
    }

    if (nextFilters === appliedFilters) {
      await usersQuery.refetch();
    }
    setSelectedUserId(nextSelectedUserId);
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

  const userActionMutation = useMutation({
    mutationFn: async ({
      action,
      userId,
      stepUpToken,
    }: {
      action: 'revoke' | 'restore';
      userId: string;
      stepUpToken: string;
    }) => {
      if (!accessToken) {
        throw new Error('Missing admin session');
      }

      return action === 'revoke'
        ? revokeAdminUser(accessToken, userId, stepUpToken)
        : restoreAdminUser(accessToken, userId, stepUpToken);
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

  const userUpdateMutation = useMutation({
    mutationFn: async ({
      userId,
      payload,
      stepUpToken,
    }: {
      userId: string;
      payload: AdminUserUpdateRequest;
      stepUpToken?: string | null;
    }) => {
      if (!accessToken) {
        throw new Error('Missing admin session');
      }

      return updateAdminUser(accessToken, userId, payload, stepUpToken);
    },
    onMutate: () => {
      setActionFeedback(null);
      setActionError(null);
    },
    onSuccess: async (_response, variables) => {
      try {
        await refreshUsersState(variables.userId);
        setActionFeedback('User changes saved. The list and detail panel were refreshed from the backend.');
      } catch (error) {
        if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
          handleExpiredSession();
          navigate('/login', { replace: true, state: { from: '/users' } });
          return;
        }

        setActionError('User changes were saved, but the follow-up refresh failed. Retry the list or detail query.');
      }
    },
  });

  const userCreateMutation = useMutation({
    mutationFn: async ({
      payload,
      stepUpToken,
    }: {
      payload: AdminUserCreateRequest;
      stepUpToken?: string | null;
    }) => {
      if (!accessToken) {
        throw new Error('Missing admin session');
      }

      return createAdminUser(accessToken, payload, stepUpToken);
    },
    onMutate: () => {
      setCreateFormError(null);
      setActionFeedback(null);
      setActionError(null);
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

  useEffect(() => {
    setEditDraft(formatUserEditDraft(detailQuery.data));
  }, [detailQuery.data]);

  const isRevoking = userActionMutation.isPending && userActionMutation.variables?.action === 'revoke';
  const isRestoring = userActionMutation.isPending && userActionMutation.variables?.action === 'restore';
  const isSavingChanges = userUpdateMutation.isPending;
  const isCreatingUser = userCreateMutation.isPending;
  const selectedDetail = detailQuery.data;
  const selectedUserIsRevoked =
    selectedDetail?.status === 'revoked' || selectedDetail?.license_status === 'revoked';

  async function runUserAction(action: 'revoke' | 'restore', userId: string): Promise<void> {
    try {
      const stepUpToken = await requestStepUp({
        scope: ADMIN_STEP_UP_SCOPE_USERS_WRITE,
        actionLabel: action === 'revoke' ? 'Revoke user' : 'Restore user',
        description:
          action === 'revoke'
            ? 'Confirm your password before revoking this user. The admin API will issue a short-lived step-up token for the destructive request.'
            : 'Confirm your password before restoring this user. The admin API will issue a short-lived step-up token for the destructive request.',
      });
      await userActionMutation.mutateAsync({ action, userId, stepUpToken });
    } catch (error) {
      if (isAdminStepUpCancelledError(error)) {
        return;
      }
    }
  }

  async function runUserUpdate(user: AdminUserRecord): Promise<void> {
    const payload = buildUserUpdatePayload(user, editDraft);
    if (Object.keys(payload).length === 0) {
      setActionError(null);
      setActionFeedback('No user changes to save.');
      return;
    }

    try {
      await userUpdateMutation.mutateAsync({ userId: user.id, payload });
    } catch (error) {
      if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
        handleExpiredSession();
        navigate('/login', { replace: true, state: { from: '/users' } });
        return;
      }

      if (
        error instanceof AdminApiError &&
        (error.errorCode === 'step_up_required' ||
          error.errorCode === 'step_up_invalid' ||
          error.errorCode === 'step_up_expired')
      ) {
        try {
          const stepUpToken = await requestStepUp({
            scope: ADMIN_STEP_UP_SCOPE_USERS_WRITE,
            actionLabel: 'Save user changes',
            description:
              'Confirm your password before saving sensitive user changes. The admin API will issue a short-lived step-up token for the protected update request.',
          });
          await userUpdateMutation.mutateAsync({ userId: user.id, payload, stepUpToken });
          return;
        } catch (stepUpError) {
          if (isAdminStepUpCancelledError(stepUpError)) {
            return;
          }

          if (stepUpError instanceof AdminApiError && isAuthExpiredError(stepUpError.errorCode)) {
            handleExpiredSession();
            navigate('/login', { replace: true, state: { from: '/users' } });
            return;
          }

          throw stepUpError;
        }
      }

      setActionError(error instanceof AdminApiError ? mapAdminActionError(error.errorCode) : mapAdminActionError());
    }
  }

  async function handleCreateUserSuccess(createdUserId: string): Promise<void> {
    try {
      await refreshUsersState(createdUserId, { revealInDefaultList: true });
      createForm.resetFields();
      createForm.setFieldsValue(EMPTY_CREATE_USER_FORM_VALUES);
      setCreateFormError(null);
      setCreateModalOpen(false);
      setActionFeedback('User created. The list and detail panel were refreshed from the backend.');
    } catch (error) {
      if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
        handleExpiredSession();
        navigate('/login', { replace: true, state: { from: '/users' } });
        return;
      }

      setActionError('User was created, but the follow-up refresh failed. Retry the list or detail query.');
    }
  }

  async function runUserCreate(values: CreateUserFormValues): Promise<void> {
    const payload = buildUserCreatePayload(values);
    createForm.setFields(
      (Object.keys(EMPTY_CREATE_USER_FORM_VALUES) as Array<keyof CreateUserFormValues>).map((name) => ({
        name,
        errors: [],
      }))
    );

    try {
      const createdUser = await userCreateMutation.mutateAsync({ payload });
      await handleCreateUserSuccess(createdUser.id);
      return;
    } catch (error) {
      if (error instanceof AdminApiError && isAuthExpiredError(error.errorCode)) {
        handleExpiredSession();
        navigate('/login', { replace: true, state: { from: '/users' } });
        return;
      }

      if (
        error instanceof AdminApiError &&
        (error.errorCode === 'step_up_required' ||
          error.errorCode === 'step_up_invalid' ||
          error.errorCode === 'step_up_expired')
      ) {
        try {
          const stepUpToken = await requestStepUp({
            scope: ADMIN_STEP_UP_SCOPE_USERS_WRITE,
            actionLabel: 'Create user',
            description:
              'Confirm your password before creating a managed user. The admin API will issue a short-lived step-up token for the protected create request.',
          });
          const createdUser = await userCreateMutation.mutateAsync({ payload, stepUpToken });
          await handleCreateUserSuccess(createdUser.id);
          return;
        } catch (stepUpError) {
          if (isAdminStepUpCancelledError(stepUpError)) {
            return;
          }

          if (stepUpError instanceof AdminApiError && isAuthExpiredError(stepUpError.errorCode)) {
            handleExpiredSession();
            navigate('/login', { replace: true, state: { from: '/users' } });
            return;
          }

          if (applyValidationErrorsToForm(createForm, stepUpError)) {
            return;
          }

          setCreateFormError(
            stepUpError instanceof AdminApiError ? mapAdminActionError(stepUpError.errorCode) : mapAdminActionError()
          );
          return;
        }
      }

      if (applyValidationErrorsToForm(createForm, error)) {
        return;
      }

      setCreateFormError(error instanceof AdminApiError ? mapAdminActionError(error.errorCode) : mapAdminActionError());
    }
  }

  if (!accessToken) {
    return <ErrorState title="Admin session missing" description={formatAdminMissingSession('users')} />;
  }

  if (usersQuery.isLoading && !usersQuery.data) {
    return <LoadingState title="Loading managed users" />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Flex justify="space-between" align="flex-start" gap={16} wrap="wrap">
        <div>
          <Typography.Title level={2} style={{ marginBottom: 8 }}>
            Users
          </Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            Search and review managed users, then create, edit, revoke, or restore access with role-aware safeguards and backend-backed refresh.
          </Typography.Paragraph>
        </div>
        <Button
          type="primary"
          disabled={!canWrite || isCreatingUser || isSavingChanges || isRevoking || isRestoring}
          onClick={() => {
            setActionFeedback(null);
            setActionError(null);
            setCreateFormError(null);
            createForm.resetFields();
            createForm.setFieldsValue(EMPTY_CREATE_USER_FORM_VALUES);
            setCreateModalOpen(true);
          }}
        >
          Create user
        </Button>
      </Flex>

      <Alert
        type={canWrite ? 'success' : 'warning'}
        showIcon
        message={canWrite ? 'Write access available' : 'Read-only access'}
        description={
          canWrite
            ? 'Create, revoke, and restore actions reuse backend step-up verification. Display name changes save directly, while sensitive license and entitlement updates request password confirmation only when the backend requires it.'
            : 'This role can review users, but create, edit, revoke, and restore controls remain disabled.'
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
          <OffsetPaginationControls
            filters={appliedFilters}
            response={usersQuery.data}
            loading={usersQuery.isFetching}
            onChange={applyPagination}
          />
          {usersQuery.isError ? (
            <ErrorState
              title="User list unavailable"
              description={formatAdminListError('user')}
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
            <EmptyState description={formatFilteredEmptyState('users')} />
          )}
        </Card>

        <Card title="Selected user" style={{ flex: '2 1 480px', minWidth: 360 }}>
          {detailQuery.isLoading ? (
            <LoadingState title="Loading selected user" />
          ) : detailQuery.isError ? (
            <ErrorState
              title="User detail unavailable"
              description={formatAdminDetailError('user')}
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

              <Card size="small" title="Edit user">
                <Form
                  layout="vertical"
                  onFinish={() => {
                    if (!selectedDetail) return;
                    setActionFeedback(null);
                    setActionError(null);
                    void runUserUpdate(selectedDetail);
                  }}
                >
                  <Flex gap={16} wrap="wrap" align="end">
                    <Form.Item label="Display name" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
                      <Input
                        aria-label="Display name"
                        value={editDraft.displayName}
                        placeholder="Alice"
                        disabled={!canWrite || isSavingChanges || isRevoking || isRestoring}
                        onChange={(event) =>
                          setEditDraft((current) => ({
                            ...current,
                            displayName: event.target.value,
                          }))
                        }
                      />
                    </Form.Item>
                    <Form.Item label="License status" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
                      <Select
                        aria-label="License status"
                        data-testid="user-license-status-select"
                        value={editDraft.licenseStatus}
                        disabled={!canWrite || isSavingChanges || isRevoking || isRestoring}
                        onChange={(value) =>
                          setEditDraft((current) => ({
                            ...current,
                            licenseStatus: value,
                          }))
                        }
                        options={[
                          { value: 'active', label: 'active' },
                          { value: 'revoked', label: 'revoked' },
                          { value: 'disabled', label: 'disabled' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item label="License expiry (ISO-8601)" style={{ minWidth: 280, flex: 1, marginBottom: 0 }}>
                      <Input
                        aria-label="License expiry (ISO-8601)"
                        value={editDraft.licenseExpiresAt}
                        placeholder="2026-07-01T00:00:00Z"
                        disabled={!canWrite || isSavingChanges || isRevoking || isRestoring}
                        onChange={(event) =>
                          setEditDraft((current) => ({
                            ...current,
                            licenseExpiresAt: event.target.value,
                          }))
                        }
                      />
                    </Form.Item>
                    <Form.Item
                      label="Entitlements (comma or newline separated)"
                      style={{ minWidth: 320, flex: '1 1 100%', marginBottom: 0 }}
                    >
                      <Input.TextArea
                        aria-label="Entitlements (comma or newline separated)"
                        autoSize={{ minRows: 2, maxRows: 4 }}
                        value={editDraft.entitlements}
                        placeholder="dashboard:view, publish:run"
                        disabled={!canWrite || isSavingChanges || isRevoking || isRestoring}
                        onChange={(event) =>
                          setEditDraft((current) => ({
                            ...current,
                            entitlements: event.target.value,
                          }))
                        }
                      />
                    </Form.Item>
                    <Space>
                      <Button
                        type="primary"
                        htmlType="submit"
                        disabled={!canWrite || isRevoking || isRestoring}
                        loading={isSavingChanges}
                      >
                        Save changes
                      </Button>
                      <Button
                        disabled={!canWrite || isSavingChanges || isRevoking || isRestoring}
                        onClick={() => {
                          setActionFeedback(null);
                          setActionError(null);
                          setEditDraft(formatUserEditDraft(selectedDetail));
                        }}
                      >
                        Reset
                      </Button>
                    </Space>
                  </Flex>
                </Form>
              </Card>

              <Flex gap={12} wrap="wrap">
                <Button
                  danger
                  disabled={!canWrite || isRevoking || isRestoring || isSavingChanges}
                  loading={isRevoking}
                  onClick={() => {
                    if (!selectedDetail) return;
                    void runUserAction('revoke', selectedDetail.id);
                  }}
                >
                  Revoke user
                </Button>
                <Button
                  disabled={!canWrite || isRevoking || isRestoring || isSavingChanges}
                  loading={isRestoring}
                  onClick={() => {
                    if (!selectedDetail) return;
                    void runUserAction('restore', selectedDetail.id);
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
                    ? 'Create plus sensitive edit, revoke, and restore actions are audited server-side. Protected flows require password confirmation, a short-lived step-up token, and a backend refresh after success.'
                    : 'This role can review users, but create, edit, revoke, and restore actions remain disabled.'
                }
              />
            </Space>
          ) : usersQuery.isFetching ? (
            <LoadingState title="Refreshing user detail" />
          ) : selectedUser ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={formatSelectionEmptyState('a user', 'authorization detail')}
            />
          ) : (
            <EmptyState description={formatSelectionEmptyState('a user', 'authorization detail')} />
          )}
        </Card>
      </Flex>
      <Modal
        open={createModalOpen}
        title="Create user"
        onCancel={() => {
          if (isCreatingUser) {
            return;
          }
          setCreateFormError(null);
          createForm.resetFields();
          createForm.setFieldsValue(EMPTY_CREATE_USER_FORM_VALUES);
          setCreateModalOpen(false);
        }}
        destroyOnHidden
        footer={null}
        maskClosable={!isCreatingUser}
        closable={!isCreatingUser}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            Create a managed user with an initial password, baseline license state, and entitlements. The list and detail panel will refresh after a successful create.
          </Typography.Paragraph>

          {createFormError ? <Alert type="error" showIcon message={createFormError} /> : null}

          <Form<CreateUserFormValues>
            form={createForm}
            layout="vertical"
            initialValues={EMPTY_CREATE_USER_FORM_VALUES}
            onValuesChange={() => setCreateFormError(null)}
            onFinish={(values) => {
              void runUserCreate(values);
            }}
          >
            <Form.Item
              label="Username"
              name="username"
              rules={[{ required: true, message: 'Please enter a username.' }]}
            >
              <Input placeholder="alice2" disabled={isCreatingUser} />
            </Form.Item>

            <Form.Item
              label="Initial password"
              name="password"
              rules={[
                { required: true, message: 'Please enter an initial password.' },
                { min: 8, message: 'Use at least 8 characters for the initial password.' },
              ]}
            >
              <Input.Password autoComplete="new-password" placeholder="TempSecret123!" disabled={isCreatingUser} />
            </Form.Item>

            <Flex gap={16} wrap="wrap" align="start">
              <Form.Item label="Display name" name="display_name" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
                <Input placeholder="Alice Example" disabled={isCreatingUser} />
              </Form.Item>
              <Form.Item label="Email" name="email" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
                <Input placeholder="alice@example.com" disabled={isCreatingUser} />
              </Form.Item>
            </Flex>

            <Flex gap={16} wrap="wrap" align="start" style={{ marginTop: 16 }}>
              <Form.Item label="Tenant ID" name="tenant_id" style={{ minWidth: 220, flex: 1, marginBottom: 0 }}>
                <Input placeholder="tenant_1" disabled={isCreatingUser} />
              </Form.Item>
              <Form.Item
                label="License status"
                name="license_status"
                style={{ minWidth: 220, flex: 1, marginBottom: 0 }}
              >
                <Select
                  disabled={isCreatingUser}
                  options={[
                    { value: 'active', label: 'active' },
                    { value: 'revoked', label: 'revoked' },
                    { value: 'disabled', label: 'disabled' },
                  ]}
                />
              </Form.Item>
            </Flex>

            <Form.Item
              label="License expiry (ISO-8601)"
              name="license_expires_at"
              style={{ marginBottom: 16, marginTop: 16 }}
            >
              <Input placeholder="2026-07-01T00:00:00Z" disabled={isCreatingUser} />
            </Form.Item>

            <Form.Item
              label="Entitlements (comma or newline separated)"
              name="entitlements"
              style={{ marginBottom: 0 }}
            >
              <Input.TextArea
                autoSize={{ minRows: 2, maxRows: 4 }}
                placeholder="dashboard:view, publish:run"
                disabled={isCreatingUser}
              />
            </Form.Item>

            <Space style={{ width: '100%', justifyContent: 'flex-end', marginTop: 24 }}>
              <Button
                onClick={() => {
                  setCreateFormError(null);
                  createForm.resetFields();
                  createForm.setFieldsValue(EMPTY_CREATE_USER_FORM_VALUES);
                  setCreateModalOpen(false);
                }}
                disabled={isCreatingUser}
              >
                Cancel
              </Button>
              <Button type="primary" htmlType="submit" loading={isCreatingUser}>
                Create user
              </Button>
            </Space>
          </Form>
        </Space>
      </Modal>
      {stepUpModal}
    </Space>
  );
}
