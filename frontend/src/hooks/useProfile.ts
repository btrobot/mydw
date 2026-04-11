/**
 * Profile Hooks - 合成配置档相关的 React Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import {
  listProfilesApiProfilesGet,
  createProfileApiProfilesPost,
  updateProfileApiProfilesProfileIdPut,
  deleteProfileApiProfilesProfileIdDelete,
  setDefaultProfileApiProfilesProfileIdSetDefaultPut,
} from '@/api'
import type {
  PublishProfileCreate,
  PublishProfileListResponse,
  PublishProfileUpdate,
} from '@/api'

export type {
  CompositionMode,
  PublishProfileCreate,
  PublishProfileListResponse,
  PublishProfileResponse,
  PublishProfileUpdate,
} from '@/api'

// ============ Error helper ============

function handleError(error: unknown, fallback: string): void {
  if (error instanceof Error) {
    message.error(error.message)
  } else {
    message.error(fallback)
  }
}

// ============ Hooks ============

export const useProfiles = () =>
  useQuery<PublishProfileListResponse>({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await listProfilesApiProfilesGet()
      return response.data!
    },
  })

export const useCreateProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: PublishProfileCreate) => {
      const response = await createProfileApiProfilesPost({ body: data })
      return response.data!
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      message.success('配置档创建成功')
    },
    onError: (error: unknown) => handleError(error, '创建失败'),
  })
}

export const useUpdateProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: PublishProfileUpdate }) => {
      const response = await updateProfileApiProfilesProfileIdPut({
        path: { profile_id: id },
        body: data,
      })
      return response.data!
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      message.success('配置档更新成功')
    },
    onError: (error: unknown) => handleError(error, '更新失败'),
  })
}

export const useDeleteProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await deleteProfileApiProfilesProfileIdDelete({ path: { profile_id: id } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      message.success('配置档删除成功')
    },
    onError: (error: unknown) => handleError(error, '删除失败'),
  })
}

export const useSetDefaultProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await setDefaultProfileApiProfilesProfileIdSetDefaultPut({
        path: { profile_id: id },
      })
      return response.data!
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      message.success('已设为默认配置档')
    },
    onError: (error: unknown) => handleError(error, '操作失败'),
  })
}
