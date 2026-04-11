/**
 * Topic Hooks — /api/topics
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listTopicsApiTopicsGet,
  createTopicApiTopicsPost,
  deleteTopicApiTopicsTopicIdDelete,
  searchTopicsApiTopicsSearchGet,
  getGlobalTopicsApiTopicsGlobalGet,
  setGlobalTopicsApiTopicsGlobalPut,
  batchDeleteTopicsApiTopicsBatchDeletePost,
  listTopicGroupsApiTopicGroupsGet,
  getTopicGroupApiTopicGroupsGroupIdGet,
  createTopicGroupApiTopicGroupsPost,
  updateTopicGroupApiTopicGroupsGroupIdPut,
  deleteTopicGroupApiTopicGroupsGroupIdDelete,
} from '@/api'
import type {
  GlobalTopicResponse,
  TopicCreate,
  TopicListResponse,
  TopicGroupResponse,
  TopicGroupCreate,
  TopicGroupUpdate,
  TopicGroupListResponse,
  TopicResponse,
} from '@/api'
import type { BatchDeleteResponse } from '@/types/material'

export const useTopics = (params?: { keyword?: string; source?: string }) =>
  useQuery<TopicResponse[]>({
    queryKey: ['topics', params],
    queryFn: async () => {
      const response = await listTopicsApiTopicsGet({ query: params })
      return (response.data as TopicListResponse).items
    },
  })

export const useCreateTopic = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: TopicCreate) => {
      const response = await createTopicApiTopicsPost({ body: payload })
      return response.data!
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
      await deleteTopicApiTopicsTopicIdDelete({ path: { topic_id: topicId } })
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
      const response = await searchTopicsApiTopicsSearchGet({ query: { keyword } })
      return (response.data as TopicListResponse).items
    },
    enabled: keyword.trim().length > 0,
  })

export const useGlobalTopics = () =>
  useQuery<GlobalTopicResponse>({
    queryKey: ['topics', 'global'],
    queryFn: async () => {
      const response = await getGlobalTopicsApiTopicsGlobalGet()
      return response.data as GlobalTopicResponse
    },
  })

export const useSetGlobalTopics = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (topic_ids: number[]) => {
      const response = await setGlobalTopicsApiTopicsGlobalPut({ body: { topic_ids } })
      return response.data as GlobalTopicResponse
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
      const response = await batchDeleteTopicsApiTopicsBatchDeletePost({ body: { ids } })
      return response.data as BatchDeleteResponse
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
      const response = await listTopicGroupsApiTopicGroupsGet()
      return (response.data as TopicGroupListResponse).items
    },
  })

export const useTopicGroup = (id: number) =>
  useQuery<TopicGroupResponse>({
    queryKey: ['topic-groups', id],
    queryFn: async () => {
      const response = await getTopicGroupApiTopicGroupsGroupIdGet({ path: { group_id: id } })
      return response.data!
    },
    enabled: !!id,
  })

export const useCreateTopicGroup = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: TopicGroupCreate) => {
      const response = await createTopicGroupApiTopicGroupsPost({ body: payload })
      return response.data!
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
      const response = await updateTopicGroupApiTopicGroupsGroupIdPut({
        path: { group_id: id },
        body: payload,
      })
      return response.data!
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
      await deleteTopicGroupApiTopicGroupsGroupIdDelete({ path: { group_id: id } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topic-groups'] })
    },
  })
}
