/**
 * Video Hooks — /api/videos
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { VideoResponse, VideoListResponse, VideoCreate } from '@/types/material'

export const useVideos = (productId?: number) =>
  useQuery<VideoResponse[]>({
    queryKey: ['videos', productId],
    queryFn: async () => {
      const params = productId !== undefined ? { product_id: productId } : {}
      const { data } = await api.get<VideoListResponse>('/videos', { params })
      return data.items
    },
  })

export const useCreateVideo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: VideoCreate) => {
      const { data } = await api.post<VideoResponse>('/videos', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export const useDeleteVideo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (videoId: number) => {
      await api.delete(`/videos/${videoId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}
