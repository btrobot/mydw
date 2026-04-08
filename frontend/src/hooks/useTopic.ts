/**
 * Topic Hooks — /api/topics
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type {
  TopicResponse,
  TopicListResponse,
  TopicCreate,
  GlobalTopicsResponse,
  SetGlobalTopicsRequest,
  BatchDeleteResponse,
  TopicGroupResponse,
  TopicGroupListResponse,
  TopicGroupCreate,
  TopicGroupUpdate,
} from '@/types/material'

export const useTopics = (params?: { keyword?: string; source?: string }) =>
  useQuery<TopicResponse[]>({
    queryKey: ['topics', params],
    queryFn: async () => {
      const { data } = await api.get<TopicListResponse>('/topics', { params })
      return data.items
    },
  })

export const useCreateTopic = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: TopicCreate) => {
      const { data } = await api.post<TopicResponse>('/topics', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topics'] })
    },
  })
}

export const useDeleteTopic = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (topicId: number) => {
      await api.delete(`/topics/${topicId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topics'] })
    },
  })
}

export const useSearchTopics = (keyword: string) =>
  useQuery<TopicResponse[]>({
    queryKey: ['topics', 'search', keyword],
    queryFn: async () => {
      const { data } = await api.get<TopicListResponse>('/topics/search', { params: { keyword } })
      return data.items
    },
    enabled: keyword.trim().length > 0,
  })

export const useGlobalTopics = () =>
  useQuery<GlobalTopicsResponse>({
    queryKey: ['topics', 'global'],
    queryFn: async () => {
      const { data } = await api.get<GlobalTopicsResponse>('/topics/global')
      return data
    },
  })

export const useSetGlobalTopics = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: SetGlobalTopicsRequest) => {
      const { data } = await api.put<GlobalTopicsResponse>('/topics/global', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topics', 'global'] })
    },
  })
}

export const useBatchDeleteTopics = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) => {
      const { data } = await api.post<BatchDeleteResponse>('/topics/batch-delete', { ids })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topics'] })
    },
  })
}

export const useTopicGroups = () =>
  useQuery<TopicGroupResponse[]>({
    queryKey: ['topic-groups'],
    queryFn: async () => {
      const { data } = await api.get<TopicGroupListResponse>('/topic-groups')
      return data.items
    },
  })

export const useTopicGroup = (id: number) =>
  useQuery<TopicGroupResponse>({
    queryKey: ['topic-groups', id],
    queryFn: async () => {
      const { data } = await api.get<TopicGroupResponse>(`/topic-groups/${id}`)
      return data
    },
    enabled: !!id,
  })

export const useCreateTopicGroup = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: TopicGroupCreate) => {
      const { data } = await api.post<TopicGroupResponse>('/topic-groups', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topic-groups'] })
    },
  })
}

export const useUpdateTopicGroup = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: TopicGroupUpdate }) => {
      const { data } = await api.put<TopicGroupResponse>(`/topic-groups/${id}`, payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topic-groups'] })
    },
  })
}

export const useDeleteTopicGroup = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/topic-groups/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topic-groups'] })
    },
  })
}
