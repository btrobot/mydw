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

export const useAccounts = () =>
  useQuery<AccountResponse[]>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const response = await listAccountsApiAccountsGet()
      return response.data ?? []
    },
  })

export const useAccount = (accountId: number) =>
  useQuery<AccountResponse>({
    queryKey: ['account', accountId],
    queryFn: async () => {
      const response = await getAccountApiAccountsAccountIdGet({ path: { account_id: accountId } })
      return response.data!
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
