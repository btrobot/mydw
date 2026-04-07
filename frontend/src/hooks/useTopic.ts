/**
 * Topic Hooks — /api/topics
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { TopicResponse, TopicListResponse, TopicCreate } from '@/types/material'

export const useTopics = (sort?: string) =>
  useQuery<TopicResponse[]>({
    queryKey: ['topics', sort],
    queryFn: async () => {
      const params = sort ? { sort } : {}
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
