/**
 * Profile Hooks - 合成配置档相关的 React Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { message } from 'antd'
import { api } from '@/services/api'

// ============ Types ============

export type CompositionMode = 'none' | 'coze' | 'local_ffmpeg'

export interface PublishProfileResponse {
  id: number
  name: string
  is_default: boolean
  composition_mode: CompositionMode
  coze_workflow_id: string | null
  composition_params: string | null
  global_topic_ids: number[]
  auto_retry: boolean
  max_retry_count: number
  created_at: string
  updated_at: string
}

export interface PublishProfileListResponse {
  total: number
  items: PublishProfileResponse[]
}

export interface PublishProfileCreate {
  name: string
  is_default?: boolean
  composition_mode?: CompositionMode
  coze_workflow_id?: string | null
  composition_params?: string | null
  global_topic_ids?: number[]
  auto_retry?: boolean
  max_retry_count?: number
}

export interface PublishProfileUpdate {
  name?: string
  is_default?: boolean
  composition_mode?: CompositionMode
  coze_workflow_id?: string | null
  composition_params?: string | null
  global_topic_ids?: number[]
  auto_retry?: boolean
  max_retry_count?: number
}

// ============ Error helper ============

function handleError(error: unknown, fallback: string): void {
  if (axios.isAxiosError(error)) {
    message.error(error.response?.data?.detail || error.message)
  } else if (error instanceof Error) {
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
      const response = await api.get<PublishProfileListResponse>('/profiles')
      return response.data
    },
  })

export const useCreateProfile = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: PublishProfileCreate) => {
      const response = await api.post<PublishProfileResponse>('/profiles', data)
      return response.data
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
      const response = await api.put<PublishProfileResponse>(`/profiles/${id}`, data)
      return response.data
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
      await api.delete(`/profiles/${id}`)
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
      const response = await api.put<PublishProfileResponse>(`/profiles/${id}/set-default`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      message.success('已设为默认配置档')
    },
    onError: (error: unknown) => handleError(error, '操作失败'),
  })
}
