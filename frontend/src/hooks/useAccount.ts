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
  loginAccountApiAccountsLoginAccountIdPost,
  testAccountApiAccountsTestAccountIdPost,
} from '@/api'

import type {
  AccountResponse,
  AccountStats,
  AccountCreate,
  AccountUpdate,
} from '@/api'

/**
 * Extended account response that includes fields added after initial code generation.
 * phone_masked is provided by the backend when a phone number has been stored.
 */
export interface AccountResponseExtended extends AccountResponse {
  phone_masked?: string | null
  dewu_nickname?: string | null
  dewu_uid?: string | null
  avatar_url?: string | null
  tags?: string[]
  remark?: string | null
  session_expires_at?: string | null
  last_health_check?: string | null
  login_fail_count?: number
}

export interface AccountQueryParams {
  status?: string
  tag?: string
  search?: string
}

export const useAccounts = (params?: AccountQueryParams) =>
  useQuery<AccountResponseExtended[]>({
    queryKey: ['accounts', params],
    queryFn: async () => {
      // Use the generated client when no extra params are needed, otherwise
      // fall back to the axios instance which supports tag/search (added
      // backend-side after the client was last generated).
      if (!params?.tag && !params?.search) {
        const response = await listAccountsApiAccountsGet(
          params?.status ? { query: { status: params.status } } : undefined,
        )
        return (response.data ?? []) as AccountResponseExtended[]
      }

      // Import lazily to avoid circular dependency issues
      const { api } = await import('@/services/api')
      const searchParams = new URLSearchParams()
      if (params?.status) searchParams.set('status', params.status)
      if (params?.tag) searchParams.set('tag', params.tag)
      if (params?.search) searchParams.set('search', params.search)
      const { data } = await api.get<AccountResponseExtended[]>(
        `/accounts/?${searchParams.toString()}`,
      )
      return data ?? []
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
    mutationFn: async (accountId: number) => {
      const response = await loginAccountApiAccountsLoginAccountIdPost({ path: { account_id: accountId } })
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
