/**
 * Account Hooks - 账号相关的 React Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listAccountsApiAccountsGet,
  createAccountApiAccountsPost,
  getAccountApiAccountsAccountIdGet,
  updateAccountApiAccountsAccountIdPut,
  deleteAccountApiAccountsAccountIdDelete,
  getAccountStatsApiAccountsStatsGet,
  loginAccountDeprecatedApiAccountsLoginAccountIdPost,
  testAccountApiAccountsTestAccountIdPost,
  previewAccountApiAccountsAccountIdPreviewPost,
  closePreviewApiAccountsAccountIdPreviewClosePost,
  previewStatusApiAccountsPreviewStatusGet,
  healthCheckApiAccountsAccountIdHealthCheckPost,
  batchHealthCheckApiAccountsBatchHealthCheckPost,
  batchHealthCheckStatusApiAccountsBatchHealthCheckStatusGet,
} from '@/api'

import type {
  AccountResponse,
  AccountStats,
  AccountCreate,
  AccountUpdate,
  ConnectionRequest,
  PreviewActionResponse,
  PreviewStatusResponse,
  HealthCheckResponse,
  BatchHealthCheckResponse,
  BatchHealthCheckStatusResponse,
} from '@/api'

export type AccountResponseExtended = AccountResponse

export interface AccountQueryParams {
  status?: string
  tag?: string
  search?: string
}

export const useAccounts = (params?: AccountQueryParams) =>
  useQuery<AccountResponseExtended[]>({
    queryKey: ['accounts', params],
    queryFn: async () => {
      const response = await listAccountsApiAccountsGet({
        query: {
          status: params?.status,
          tag: params?.tag,
          search: params?.search,
        },
      })
      return (response.data ?? []) as AccountResponseExtended[]
    },
  })

export const useAccount = (accountId: number) =>
  useQuery<AccountResponseExtended>({
    queryKey: ['account', accountId],
    queryFn: async () => {
      const response = await getAccountApiAccountsAccountIdGet({ path: { account_id: accountId } })
      return response.data as AccountResponseExtended
    },
    enabled: !!accountId,
  })

export const useCreateAccount = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: AccountCreate) => {
      const response = await createAccountApiAccountsPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export const useUpdateAccount = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ accountId, data }: { accountId: number; data: AccountUpdate }) => {
      const response = await updateAccountApiAccountsAccountIdPut({ path: { account_id: accountId }, body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export const useDeleteAccount = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (accountId: number) => {
      await deleteAccountApiAccountsAccountIdDelete({ path: { account_id: accountId } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export const useAccountStats = () =>
  useQuery<AccountStats>({
    queryKey: ['accountStats'],
    queryFn: async () => {
      const response = await getAccountStatsApiAccountsStatsGet()
      return response.data!
    },
  })

export const useLoginAccount = () =>
  useMutation({
    mutationFn: async ({ accountId, data }: { accountId: number; data: ConnectionRequest }) => {
      const response = await loginAccountDeprecatedApiAccountsLoginAccountIdPost({
        path: { account_id: accountId },
        body: data,
      })
      return response.data
    },
  })

export const useTestAccount = () =>
  useMutation({
    mutationFn: async (accountId: number) => {
      const response = await testAccountApiAccountsTestAccountIdPost({ path: { account_id: accountId } })
      return response.data
    },
  })

// ---------------------------------------------------------------------------
// Preview hooks
// ---------------------------------------------------------------------------

export type PreviewStatus = PreviewStatusResponse

export const usePreviewAccount = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (accountId: number) => {
      const response = await previewAccountApiAccountsAccountIdPreviewPost({
        path: { account_id: accountId },
      })
      return response.data as PreviewActionResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preview-status'] })
    },
  })
}

export const useClosePreview = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      accountId,
      saveSession,
    }: {
      accountId: number
      saveSession: boolean
    }) => {
      const response = await closePreviewApiAccountsAccountIdPreviewClosePost({
        path: { account_id: accountId },
        body: { save_session: saveSession },
      })
      return response.data as PreviewActionResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preview-status'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export const usePreviewStatus = () =>
  useQuery<PreviewStatus>({
    queryKey: ['preview-status'],
    queryFn: async () => {
      const response = await previewStatusApiAccountsPreviewStatusGet()
      return response.data as PreviewStatus
    },
    refetchInterval: 3000,
  })

// ---------------------------------------------------------------------------
// Health check hooks
// ---------------------------------------------------------------------------

export type HealthCheckResult = HealthCheckResponse
export type BatchHealthCheckResult = BatchHealthCheckResponse
export type BatchHealthCheckProgress = BatchHealthCheckStatusResponse

export const useHealthCheck = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (accountId: number) => {
      const response = await healthCheckApiAccountsAccountIdHealthCheckPost({
        path: { account_id: accountId },
      })
      return response.data as HealthCheckResult
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export const useBatchHealthCheck = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const response = await batchHealthCheckApiAccountsBatchHealthCheckPost({
        body: {},
      })
      return response.data as BatchHealthCheckResult
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export const useBatchCheckStatus = (isRunning?: boolean) =>
  useQuery<BatchHealthCheckProgress>({
    queryKey: ['batch-health-check-status'],
    queryFn: async () => {
      const response = await batchHealthCheckStatusApiAccountsBatchHealthCheckStatusGet()
      return response.data as BatchHealthCheckProgress
    },
    refetchInterval: (query) => {
      // Poll while in_progress OR while the mutation is still pending (catches the final result)
      return (query.state.data?.in_progress || isRunning) ? 1000 : false
    },
  })
